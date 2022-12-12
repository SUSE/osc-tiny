"""
Requests extension
------------------
"""
from urllib.parse import urljoin

from lxml.etree import XMLSyntaxError

from ..utils.base import ExtensionBase


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

    def update(self, request_id, **kwargs):
        """
        Update request or execute command

        .. note::

            In most cases, the API returns an XML response, so this method will try to return an
            objectified XML element. Otherwise, if parsing fails due to a syntax error, the response
            body is returned as plain text. In case of all other errors, this method lets the
            caller handle the exception.

        :param request_id: ID of the request
        :param kwargs: See Build Service
                       `API documentation <https://build.opensuse.org/apidocs/index>`_ for accepted
                       keys and values.
        :return: Response content
        :rtype: lxml.objectify.ObjectifiedElement or plain text

        .. versionadded:: 0.7.8
        """
        request_id = self._validate_id(request_id)
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path + request_id),
            method="POST",
            params=kwargs
        )
        try:
            return self.osc.get_objectified_xml(response)
        except XMLSyntaxError:
            return response.text

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

        .. deprecated:: 0.7.8

            * Replaced by :py:meth:`update`
        """
        kwargs["cmd"] = cmd
        request_id = self._validate_id(request_id)
        return self.update(request_id=request_id, **kwargs)

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
