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