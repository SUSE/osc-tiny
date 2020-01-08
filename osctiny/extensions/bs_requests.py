"""
Requests extension
------------------
"""
from __future__ import unicode_literals
from six.moves.urllib.parse import urljoin
from six import text_type

from ..utils.base import ExtensionBase


class Request(ExtensionBase):
    """
    The BuildService request API is accessible through this object.
    """
    base_path = "/request/"

    @staticmethod
    def _validate_id(request_id):
        request_id = text_type(request_id)
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
            params=params
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
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path + request_id),
            method="GET",
            params={
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
        * `addreview`: Assign a user or group to review
        * `changereviewstate`: Accept/Decline a review

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

        .. versionchanged:: 0.1.3

            * Added ``addreview`` to list of allowed commands
            * Added validation for arguments of command ``changereviewstate``
        """
        allowed_cmds = ['diff', 'changereviewstate', 'addreview']
        allowed_review_states = ['new', 'accepted', 'declined', 'deleted',
                                 'revoked', 'superseded']
        if cmd not in allowed_cmds:
            raise ValueError("Invalid command: '{}'. Use one of: {}".format(
                cmd, ", ".join(allowed_cmds)
            ))

        if cmd == "changereviewstate"\
                and kwargs.get("newstate", None) not in allowed_review_states:
            raise ValueError(
                "Invalid review state: '{}'. Use one of: {}".format(
                    kwargs.get("newstate", None), allowed_review_states
                )
            )

        kwargs["cmd"] = cmd
        request_id = self._validate_id(request_id)
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path + request_id),
            method="POST",
            params=kwargs
        )

        if kwargs.get("view", "plain") == "xml":
            return self.osc.get_objectified_xml(response)
        return response.text

    def add_comment(self, request_id, comment, parent_id=None):
        """
        Add a comment to a request

        .. versionadded:: 0.1.1

        .. versionchanged:: 0.1.8
            Use internally :py:class:`osctiny.comments.Comment.add`

        :param request_id: ID of the request
        :param comment: Comment to be added
        :param parent_id: ID of parent comment. Default: ``None``
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        return self.osc.comments.add(
            obj_type="request",
            ids=(request_id,),
            comment=comment,
            parent_id=parent_id
        )

    def get_comments(self, request_id):
        """
        Get a list of comments for request

        .. versionchanged:: 0.1.8
            Use internally :py:class:`osctiny.comments.Comment.get`

        :param request_id: ID of the request
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self.osc.comments.get(
            obj_type="request",
            ids=(request_id,)
        )
