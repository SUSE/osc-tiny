"""
Issues extension
----------------
"""
from __future__ import unicode_literals
import os

from six.moves.urllib.parse import urljoin
from six import text_type

from ..utils.backports import lru_cache
from ..utils.base import ExtensionBase


class Issue(ExtensionBase):
    """
    The BuildService issue(-tracker) API is accessible through this object.

    .. versionadded:: 0.2.2
    """
    base_path = "/issue_trackers/"

    @staticmethod
    def _validate(value):
        return text_type(value)

    @lru_cache(maxsize=1)
    def get_trackers(self):
        """
        Get all issue trackers with data
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path),
            method="GET",
        )
        return self.osc.get_objectified_xml(response)

    def get_tracker(self, name):
        """
        Get information on one issue tracker

        :param str name: issue tracker name
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, os.path.join(self.base_path, name)),
            method="GET",
        )
        return self.osc.get_objectified_xml(response)

    def get(self, tracker, name, force_update=None):
        """
        Get details for an issue

        :param str tracker: issue tracker name
        :param str name: issue name
        :param force_update: If ``True``, BuildService will update the issue
                             details internally prior to returning the response
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        tracker, name = [self._validate(x) for x in [tracker, name]]
        trackers = self.get_trackers()
        can_get_details = trackers.xpath(
            "issue-tracker/name[text()='{}']/../enable-fetch".format(tracker))

        response = self.osc.request(
            url=urljoin(self.osc.url,
                        os.path.join(self.base_path, tracker, "issues", name)),
            method="GET",
            params={'force_update': force_update}
        )
        response = self.osc.get_objectified_xml(response)

        if not force_update and can_get_details and all(can_get_details):
            if not getattr(getattr(response, "summary", None), "text", None):
                return self.get(tracker, name, force_update=True)

        return response
