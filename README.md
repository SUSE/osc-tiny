OSC Tiny
========

[![Build Status](https://travis-ci.com/crazyscientist/osc-tiny.svg?branch=master)](https://travis-ci.com/crazyscientist/osc-tiny)

This project aims to provide a minimalistic and transparent client for accessing
the [OpenBuildService](https://openbuildservice.org/) 
[API](https://build.opensuse.org/apidocs/index).

Usage
-----

This is a very basic example:

```python
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
```

For more documentation see https://osc-tiny.readthedocs.io/en/latest/

Contributing
------------

Any contributions are welcome.

Links
-----

* https://osc-tiny.readthedocs.io/en/latest/
* https://openbuildservice.org/
* https://build.opensuse.org/apidocs/index