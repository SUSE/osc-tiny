"""
Comments extension
------------------
"""
import os
from urllib.parse import urljoin

from ..utils.base import ExtensionBase


class Comment(ExtensionBase):
    """
    The BuildService comment(s) API is accessible through this object.
    """
    base_path = "/comments/"
    allowed_object_types = {"project": 1, "package": 2, "request": 1}

    def _validate(self, obj_type, ids):
        if obj_type not in self.allowed_object_types:
            raise ValueError(
                "Type '{}' is not in list of allowed values: {}".format(
                    obj_type, self.allowed_object_types
                )
            )

        required_length = self.allowed_object_types.get(obj_type, -1)
        if len(ids) != required_length:
            raise ValueError("For object type {} the length of IDs has to be "
                             "equal to {}!".format(obj_type, required_length))

    def get(self, obj_type, ids):
        """
        Get a list of comments for object

        .. versionadded:: 0.1.8

        .. note::

            The ``ids`` argument will look like this, e.g. for a package:
            ``('project_name', 'package_name')``.


        :param obj_type: Name of object type (project, package, request)
        :type obj_type: str
        :param ids: IDs of object
        :type ids: iterable
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        self._validate(obj_type, ids)
        response = self.osc.request(
            url=urljoin(self.osc.url,
                        os.path.join(*([self.base_path, obj_type]
                                       + [str(x) for x in ids]))),
            method="GET",
        )
        return self.osc.get_objectified_xml(response)

    def add(self, obj_type, ids, comment, parent_id=None):
        """
        Add a comment to object

        :param obj_type: Name of object type (project, package, request)
        :type obj_type: str
        :param ids: IDs of object
        :type ids: iterable
        :param comment: Comment to be added
        :param parent_id: ID of parent comment. Default: ``None``
        :return: ``True``, if successful.
        :raises HTTPError: if comment was not saved correctly. The raised exception contains the
                           full response object and API response.

        .. versionadded: 0.1.8

        .. versionchanged:: 0.3.0

            Instead of simply returning the API response, if the comment was not added, an exception
            is raised.
        """
        self._validate(obj_type, ids)
        url = urljoin(self.osc.url,
                      os.path.join(*([self.base_path, obj_type] + [str(x) for x in ids])))
        params = {}
        if parent_id and str(parent_id).isnumeric():
            params["parent_id"] = parent_id

        response = self.osc.request(
            url=url,
            method="POST",
            data=comment,
            params=params,
            raise_for_status=True
        )
        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return False

    def delete(self, comment_id):
        """
        Delete comment

        .. versionadded:: 0.1.8

        :param comment_id: ID of comment
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        url = urljoin(self.osc.url, '/comment/' + str(comment_id))

        response = self.osc.request(
            url=url,
            method="DELETE",
            raise_for_status=False
        )

        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed
