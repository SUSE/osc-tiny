"""
Requests extension
------------------
"""
from urllib.parse import urljoin

from .base import ExtensionBase


class Request(ExtensionBase):
    """
    The BuildService request API is accessible through this object.
    """
    base_path = "/request/"

    @staticmethod
    def _validate_id(request_id):
        request_id = str(request_id)
        if not request_id.isnumeric():
            raise ValueError(
                "Request ID must be numeric! Got instead: {}".format(request_id)
            )
        return request_id

    def get_list(self, **params):
        """
        Get a list or request objects

        :param params: see https://build.opensuse.org/apidocs/index#73
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path),
            method="GET",
            data=params
        )

        return self.osc.get_objectified_xml(response)

    def get(self, request_id, withhistory=False, withfullhistory=False):
        """
        Get one request object

        :param request_id: ID of the request
        :param withhistory: includes the request history in result
        :type withhistory: bool
        :param withfullhistory: includes the request and review history in
                                result
        :type withfullhistory: bool
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        request_id = self._validate_id(request_id)
        withhistory = '1' if withhistory else '0'
        withfullhistory = '1' if withfullhistory else '0'
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path + request_id),
            method="GET",
            data={
                'withhistory': withhistory,
                'withfullhistory': withfullhistory
            }
        )

        return self.osc.get_objectified_xml(response)

    def cmd(self, request_id, cmd="diff", **kwargs):
        """
        Get the result of the specified command

        Available commands:

        * `diff`: Shows the diff of all affected packages.

        :param request_id: ID of the request
        :param cmd: Name of the command
        :param view: One of: ``xml`` or nothing
        :param unified: ???
        :param missingok: ???
        :param filelimit: ???
        :param expand: ???
        :param withissues: ???
        :return: plain text
        :rtype: str
        """
        allowed = ['diff', 'changereviewstate']
        if cmd not in allowed:
            raise ValueError("Invalid command: '{}'. Use one of: {}".format(
                cmd, ", ".join(allowed)
            ))

        kwargs["cmd"] = cmd
        request_id = self._validate_id(request_id)
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path + request_id),
            method="POST",
            data=kwargs
        )

        if kwargs.get("view", "plain") == "xml":
            return self.osc.get_objectified_xml(response)
        return response.text

    def add_comment(self, request_id, comment, parent_id=None):
        """
        Add a comment to a request

        .. versionadded: 0.1.1

        :param request_id: ID of the request
        :param comment: Comment to be added
        :param parent_id: ID of parent comment. Default: ``None``
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        request_id = self._validate_id(request_id)
        url = urljoin(self.osc.url, '/comments' + self.base_path + request_id)
        if parent_id and str(parent_id).isnumeric():
            url += "?parent_id={}".format(parent_id)

        response = self.osc.request(
            url=url,
            method="POST",
            data=comment
        )
        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed

    def get_comments(self, request_id):
        """
        Get a list of comments for request

        :param request_id: ID of the request
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        request_id = self._validate_id(request_id)
        response = self.osc.request(
            url=urljoin(self.osc.url,
                        '/comments' + self.base_path + request_id),
            method="GET",
        )
        return self.osc.get_objectified_xml(response)
