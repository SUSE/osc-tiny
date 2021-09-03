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

If you want to use caching, make sure to also install `CacheControl`_. It's a
purely optional feature so it is not listed in the requirements file. Use:

.. code-block:: bash

    pip install CacheControl

.. _CacheControl: https://cachecontrol.readthedocs.io/en/latest/

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