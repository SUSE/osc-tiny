OSC Tiny
========

![Build Status](https://github.com/crazyscientist/osc-tiny/actions/workflows/default.yml/badge.svg?branch=master)
![Publish Status](https://github.com/crazyscientist/osc-tiny/actions/workflows/publish.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/osc-tiny.svg)](https://badge.fury.io/py/osc-tiny)
[![Coverage badge](https://raw.githubusercontent.com/crazyscientist/osc-tiny/python-coverage-comment-action-data/badge.svg)](https://github.com/crazyscientist/osc-tiny/tree/python-coverage-comment-action-data)

This project aims to provide a minimalistic and transparent client for accessing
the [OpenBuildService](https://openbuildservice.org/) 
[API](https://build.opensuse.org/apidocs/index).

Usage
-----

This is a very basic example:

```python
from osctiny import Osc

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
