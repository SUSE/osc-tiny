Quick Start
===========

Installation
------------

Until now, the package hasn't been published on PyPi, so you can install only
from GitHub at the moment:

.. code-block:: bash

    pip install git+https://github.com/crazyscientist/osc-tiny.git

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