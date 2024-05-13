Development
===========

Releases
--------

Open Build Service
^^^^^^^^^^^^^^^^^^

To get a new release into Open Build Service (OBS) you need to perform the following steps:

* Branch the devel package ``python-osc-tiny`` from ``devel:languages:python`` into your home project and check it out locally with ``osc``
* Update the the package
  - Download the new release's gzipped tar archive from PyPI
  - Unpack it and rename the unpacked source directory from ``osc_tiny-...`` to ``osc-tiny-...`` (i.e. substitute underscore with hyphen)
  - Repack it with ``tar``, observing the same underscore-to-hyphen substitution in the output filename
  - Remove the old gzipped tar source archive and add the new one you just created with ``osc``
  - Adjust the ``.spec`` file fixing the version and potentiall any changed dependencies etc.
  - Record the new releases changelog (and potentially other pertinent changes you made) to the ``.changes`` file with ``osc vc``
  - Check the changed package in with ``osc ci``
* Check that it still builds successfully in your home project
* Submit the package, which opens a request against `devel:languages:python` to include the changes there
