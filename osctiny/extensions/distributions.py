"""
Distributions extension
-----------------------
"""
from __future__ import unicode_literals

from six.moves.urllib.parse import urljoin
from six import text_type

from ..utils.base import ExtensionBase


class Distribution(ExtensionBase):
    """
    Osc extension to interact with distributions

    .. versionadded:: 0.2.3
    """
    base_path = "/distributions"

    def get_list(self, include_remotes=False):
        """
        Get list of base distributions

        :param bool include_remotes: If ``True`` response will include distributions also from
                                     remote instances
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        url = urljoin(self.osc.url, self.base_path)
        if include_remotes:
            url += "/include_remotes"

        response = self.osc.request(
            url=url,
            method="GET"
        )

        return self.osc.get_objectified_xml(response)

    def get(self, distribution_id):
        """
        Get data of one base distributions hosted on this OBS instance

        :param int distribution_id: ID of distribution
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "/".join((self.base_path, text_type(distribution_id)))
            ),
            method="GET"
        )

        return self.osc.get_objectified_xml(response)
