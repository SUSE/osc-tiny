Release Notes
=============

0.1.3
-----

* Added ``timeout`` parameter to :py:meth:`osctiny.osc.Osc.request`

0.1.2
-----

* Added capability to add and remove attributes
* Added capability to add comments to requests
* Added capability to delete packages and projects
* Added method to check whether package, file in package or project exists
* Added support for package `aggregation`_
* Added support for revision annotations in package metadata
* Added support to upload package meta and other files
* Fixed URL for project history
* Changed request behavior:

	* Allow suppression of HTTP errors
	* Support reading of data from file handle

.. _aggregation:
    https://en.opensuse.org/openSUSE:Build_Service_Tips_and_Tricks
    #link_and_aggregate

0.1.1
-----

* Added ``changereviewstate`` to list of allowed commands on
  :py:meth:`osctiny.bs_requests.Request.cmd`
* Added capability to add comments to requests
* Added extension for build results
* Added :py:meth:`osctiny.packages.Package.checkout` to properly check-out an
  entire package
* Request parameters get encoded prior to submission to avoid decoding issues in
  the build service
* On initialization :py:class:`osctiny.Osc` accepts a ``cache`` keyword argument
  to save API responses in a cache dictionary. But requests with ``stream=True``
  are excluded from caching!