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

2FA authentication
^^^^^^^^^^^^^^^^^^

`OpenBuildService`_ supports two-factor authentication on the API. The authentication method is
based on SSH signing. If you want to use 2FA, you need a OpenSSH client. To be precise, the program
``ssh-keygen`` will be required.

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

.. code-block:: python

    from pathlib import Path
    from ostiny import Osc

    osc = Osc(
        url="https://api.opensuse.org",
        username="foobar",
        password="helloworld",
    )

    # This returns an LXML object
    osc.requests.get(request_id=1)

    # This returns an LXML object
    osc.search.request(xpath="state/@name='new'")

    # This example will use the SSH private key and passphrase for authentication
    mfa_osc = Osc(
        url="https://api.opensuse.org",
        username="foobar",
        password="secret-passphrase",
        ssh_key_file=Path("/home/nemo/.ssh/id_ed25516")
    )

Logging
-------

OSC Tiny provides a limited amount of built-in logging. To utilize this (e.g. for debugging) you
only need to `configure <https://docs.python.org/3/library/logging.config.html>` the used loggers:

osctiny.request
"""""""""""""""

Logs every HTTP request (including data and params) and response (including headers and body).
