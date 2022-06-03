"""
Authentication handlers for 2FA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.6.0
"""
import typing
from base64 import b64decode, b64encode
from pathlib import Path
from subprocess import Popen, PIPE
import re
import sys
from time import time

from requests.auth import HTTPDigestAuth
from requests.cookies import extract_cookies_to_jar
from requests.utils import parse_dict_header
from requests import Response

from .errors import OscError


class HttpSignatureAuth(HTTPDigestAuth):
    """
    Implementation of the "Signature authentication scheme"

    For reference implementation see https://github.com/openSUSE/osc/pull/1032

    :param username: The username
    :param password: Passphrase for SSH key. This can be omitted, if ``ssh-agent`` is also installed
    :param ssh_key_file: Path of SSK key
    """
    def __init__(self, username: str, password: typing.Optional[str], ssh_key_file: Path):
        super().__init__(username=username, password=password)
        if not ssh_key_file.is_file():
            raise FileNotFoundError(f"SSH key at location does not exist: {ssh_key_file}")
        self.ssh_key_file = ssh_key_file

    def __eq__(self, other: 'HttpSignatureAuth') -> bool:
        return self.ssh_key_file == getattr(other, 'ssh_key_file', None) and super().__eq__(other)

    def ssh_sign(self) -> str:
        """
        Solve the challenge via SSH signing
        """
        data = f"{self._thread_local.chal.get('headers')}: {self._thread_local.chal['now']}"
        cmd = ['ssh-keygen', '-Y', 'sign', '-f', self.ssh_key_file.as_posix(), '-q',
               '-n', self._thread_local.chal.get('realm', '')]
        if self.password:
            cmd += ['-P', self.password]
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        signature, error = proc.communicate(data.encode(sys.stdin.encoding))
        if proc.returncode:
            raise OscError(f"ssh-keygen returned {proc.returncode}: {error}")

        signature = signature
        match = re.match(br"\A-----BEGIN SSH SIGNATURE-----\n(.*)\n-----END SSH SIGNATURE-----",
                         signature, re.S)
        if not match:
            raise OscError("Could not generate challenge response")
        return b64encode(b64decode(match.group(1))).decode(sys.stdout.encoding)

    def build_digest_header(self, method: str, url: str) -> str:
        """
        Generate Authentication header
        """
        return f'Signature keyId="{self.username}",algorithm="ssh",' \
               f'headers="{self._thread_local.chal.get("headers")}",' \
               f'created={self._thread_local.chal["now"]},' \
               f'signature={self.ssh_sign()}'

    def handle_401(self, r: Response, **kwargs) -> Response:
        """
        Handle authentication in case of 401

        Contents of method copied from :py:meth:`requests.auth.HTTPDigestAuth.handle_401` and edited
        """
        if not 400 <= r.status_code < 500:
            self._thread_local.num_401_calls = 1
            return r

        if self._thread_local.pos is not None:
            # Rewind the file position indicator of the body to where
            # it was to resend the request.
            r.request.body.seek(self._thread_local.pos)
        s_auth = r.headers.get('www-authenticate', '')

        if s_auth.lower().startswith("signature") and self._thread_local.num_401_calls < 2:
            self._thread_local.num_401_calls += 1

            _, challenge = s_auth.split(" ", maxsplit=1)
            challenge = parse_dict_header(challenge)
            challenge["now"] = int(time())
            self._thread_local.chal = challenge


            r.content
            r.close()
            prep = r.request.copy()
            extract_cookies_to_jar(prep._cookies, r.request, r.raw)
            prep.prepare_cookies(prep._cookies)
            prep.headers['Authorization'] = self.build_digest_header(
                prep.method, prep.url)
            _r = r.connection.send(prep, **kwargs)
            _r.history.append(r)
            _r.request = prep

            return _r

        self._thread_local.num_401_calls = 1
        return r
