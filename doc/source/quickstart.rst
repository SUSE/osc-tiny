Quick Start
===========

Installation
------------

Simply install from PyPi:

.. code-block:: bash

    pip install osc-tiny

The impatient, who can't await a feature to be released, can install directly
from GitHub using ``pip``:

.. code-block:: bash

    pip install git+https://github.com/crazyscientist/osc-tiny.git

Strong authentication
^^^^^^^^^^^^^^^^^^^^^

`OpenBuildService`_ supports strong authentication on the API. The authentication method is
based on SSH signing. If you want to use strong authentication, you need a OpenSSH client. To be
precise, the program ``ssh-keygen`` will be required to create a signed message.

E.g. on Ubuntu you can use:

.. code-block:: shell

    sudo apt install openssh-client

.. _OpenBuildService: https://openbuildservice.org/

Caching
^^^^^^^

If you want to use caching, make sure to also install `CacheControl`_. It's a
purely optional feature so it is not listed in the requirements file. Use:

.. code-block:: bash

    pip install CacheControl

.. _CacheControl: https://cachecontrol.readthedocs.io/en/latest/

Configuration
^^^^^^^^^^^^^

If you want to use the credentials stored in the `osc`_ configuration, you can also install ``osc``
to give OSC Tiny access to it's configuration. Use one of:

.. code-block:: bash

    pip install osc
    zypper install osc
    apt install osc
    # ...

In order to install ``osc`` via the package manager on a non-SUSE distribution you will need to add
a repository from https://download.opensuse.org/repositories/openSUSE:/Tools/.

.. _osc: https://github.com/openSUSE/osc

Usage
-----

Depending on the authentication method :py:class:`osctiny.osc.Osc` gets initialized slightly
different:

.. code-block:: python

    from pathlib import Path
    from osctiny import Osc

    # Basic Auth with username + password
    osc = Osc(
        url="https://api.opensuse.org",
        username="foobar",
        password="helloworld",
    )

    # Strong auth with username + passphrase (for SSH key) + SSH key
    osc = Osc(
        url="https://api.opensuse.org",
        username="foobar",
        password="secret-passphrase",
        ssh_key_file=Path("/home/nemo/.ssh/id_ed25516")
    )

    # Strong auth with username + SSH key
    # This applies to keys without passphrase or for using the SSH agent (i.e. passphrase will be
    # queried by SSH agent)
    osc = Osc(
        url="https://api.opensuse.org",
        username="foobar",
        password=None,
        ssh_key_file=Path("/home/nemo/.ssh/id_ed25516")
    )

    # This returns an LXML object
    osc.requests.get(request_id=1)

    # This returns an LXML object
    osc.search.request(xpath="state/@name='new'")



Logging
-------

OSC Tiny provides a limited amount of built-in logging. To utilize this (e.g. for debugging) you
only need to `configure <https://docs.python.org/3/library/logging.config.html>` the used loggers:

.. list-table:: Loggers
    :header-rows: 1
    :widths: 20 80
    :width: 100%

    * - Logger
      - Description
    * - osctiny.request
      - Logs every HTTP request (including data and params)

        and response (including headers and body).
