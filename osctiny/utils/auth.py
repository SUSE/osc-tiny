"""
Authentication handlers for 2FA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.6.0
"""
import typing
from base64 import b64decode, b64encode
import logging
import os
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

    .. note::

        This seems to be a variation of the `HTTP Message Signatures`_ specification.

        See also the `reference implementation for osc`_

        .. _HTTP Message Signatures:
            https://datatracker.ietf.org/doc/draft-ietf-httpbis-message-signatures/

        .. _reference implementation for osc: https://github.com/openSUSE/osc/pull/1032

    :param username: The username
    :param password: Passphrase for SSH key. This can be omitted, if ``ssh-agent`` is also installed
    :param ssh_key_file: Path of SSK key
    """
    def __init__(self, username: str, password: typing.Optional[str], ssh_key_file: Path):
        super().__init__(username=username, password=password)
        if not ssh_key_file.is_file():
            raise FileNotFoundError(f"SSH key at location does not exist: {ssh_key_file}")
        if not password and not self.is_ssh_agent_available():
            raise RuntimeError("SSH signing impossible: No password/passphrase provided and no SSH "
                               "agent running! ")
        self.ssh_key_file = ssh_key_file
        self.pattern = re.compile(r"(?<=\)) (?=\()")

    def __eq__(self, other: 'HttpSignatureAuth') -> bool:
        return self.ssh_key_file == getattr(other, 'ssh_key_file', None) and super().__eq__(other)

    def split_headers(self, headers: str) -> typing.List[str]:
        """
        Split ``headers`` parameter from ``WWW-Authenticate Signature`` header

        :param headers: Value of the ``headers`` parameter
        """
        parts = self.pattern.split(headers)
        return [part.strip("()") for part in parts]

    @staticmethod
    def is_ssh_agent_available() -> bool:
        """
        Check whether SSH agent is running/available

        :return: ``True``, if agent is running

        .. versionadded:: 0.6.3
        """
        relevant_keys = {'SSH_AUTH_SOCK', 'SSH_AGENT_PID'}
        overlap = os.environ.keys() & relevant_keys
        return len(overlap) > 0

    def ssh_sign(self) -> str:
        """
        Solve the challenge via SSH signing
        """
        data = "\n".join(f"({header}): {self._thread_local.chal[header]}"
                         for header in self._thread_local.chal["headers"])
        cmd = ['ssh-keygen', '-Y', 'sign', '-f', self.ssh_key_file.as_posix(), '-q',
               '-n', self._thread_local.chal.get('realm', '')]
        if self.password:
            cmd += ['-P', self.password]

        encoding = sys.getdefaultencoding()
        with Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE) as proc:
            signature, error = proc.communicate(data.encode(encoding))
            if proc.returncode:
                raise OscError(f"ssh-keygen returned {proc.returncode}: {error}")

        match = re.match(br"\A-----BEGIN SSH SIGNATURE-----\n(.*)\n-----END SSH SIGNATURE-----",
                         signature, re.S)
        if not match:
            raise OscError("Could not generate challenge response")
        return b64encode(b64decode(match.group(1))).decode(encoding)

    def build_digest_header(self, method: str, url: str) -> str:
        """
        Generate Authentication header
        """
        headers = " ".join(f"({header})" for header in self._thread_local.chal["headers"])
        return f'Signature keyId="{self.username}",algorithm="ssh",signature={self.ssh_sign()},' \
               f'headers="{headers}",created={self._thread_local.chal["created"]}'

    def get_auth_header(self, r: Response) -> str:
        """
        Extract the relevant header for Signature authentication

        :param r: Response
        :return: Header text
        """
        try:
            # pylint: disable=protected-access
            headers = [header
                       for header in r.raw._original_response.headers.get_all("www-authenticate")
                       if "signature" in header.lower()]
            if headers:
                return headers[0]
        except AttributeError:
            headers = r.headers.get("www-authenticate")
            if headers:
                parts = headers.split(",")
                start = [p for p in parts if "signature" in p.lower()]
                if start:
                    start_index = parts.index(start[0])
                    return ",".join(parts[start_index:start_index + 2]).strip()

        return ""

    def _log(self, r: Response) -> None:
        logger = logging.getLogger("osctiny.request")
        if logger.level >= logging.CRITICAL:
            return

        logger.info("Server replied with status %d", r.status_code)
        logger.debug("Response headers:\n%s\n---", "\n".join(f"{k}: {v}"
                                                             for k, v in r.headers.items()))
        logger.debug("Response content:\n%s\n---", r.text)

    def handle_401(self, r: Response, **kwargs) -> Response:
        """
        Handle authentication in case of 401

        Contents of method copied from :py:meth:`requests.auth.HTTPDigestAuth.handle_401` and edited
        """
        if not 400 <= r.status_code < 500:
            self._thread_local.num_401_calls = 1
            return r

        if r.status_code != 401:
            # If this is not a 401 response, the server does not send the authentication headers.
            # So there is no point in pretending otherwise.
            return r

        self._log(r)

        if self._thread_local.pos is not None:
            # Rewind the file position indicator of the body to where
            # it was to resend the request.
            r.request.body.seek(self._thread_local.pos)
        s_auth = self.get_auth_header(r)

        if "signature" in s_auth.lower() and self._thread_local.num_401_calls < 2:
            self._thread_local.num_401_calls += 1

            _, challenge = s_auth.split(" ", maxsplit=1)
            challenge = parse_dict_header(challenge)
            challenge.setdefault("headers", ["created"])
            challenge["created"] = int(time())
            challenge["headers"] = self.split_headers(challenge["headers"])
            self._thread_local.chal.update(challenge)

            # The following is unchanged from :py:meth:`requests.auth.HTTPDigestAuth.handle_401`,
            # so we ignore linter issues about it.
            # pylint: disable=pointless-statement,protected-access
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
