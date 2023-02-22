# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/crazyscientist/osc-tiny/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                |    Stmts |     Miss |   Cover |   Missing |
|------------------------------------ | -------: | -------: | ------: | --------: |
| osctiny/\_\_init\_\_.py             |        4 |        0 |    100% |           |
| osctiny/extensions/\_\_init\_\_.py  |        0 |        0 |    100% |           |
| osctiny/extensions/bs\_requests.py  |       33 |        1 |     97% |        22 |
| osctiny/extensions/buildresults.py  |       30 |       15 |     50% |62-69, 83-90, 106-114, 138-145, 165, 184-195 |
| osctiny/extensions/comments.py      |       34 |        4 |     88% |20, 28, 85, 98 |
| osctiny/extensions/distributions.py |       13 |        0 |    100% |           |
| osctiny/extensions/issues.py        |       26 |        0 |    100% |           |
| osctiny/extensions/origin.py        |      181 |       78 |     57% |36-38, 54-68, 76, 120-121, 129-145, 174, 176, 180, 188, 248-250, 261-264, 284-285, 287, 416, 441-449, 462-466, 489-519, 529-541 |
| osctiny/extensions/packages.py      |      133 |       37 |     72% |73-80, 217-227, 256, 302-315, 376, 391, 416-437, 455-471, 550-554, 574, 577, 598, 617 |
| osctiny/extensions/projects.py      |      115 |       17 |     85% |86-88, 166, 191, 194, 251, 272, 298, 311, 331, 352-365, 414, 445 |
| osctiny/extensions/search.py        |       13 |        1 |     92% |        56 |
| osctiny/extensions/users.py         |       18 |        9 |     50% |23-32, 42-47, 65-70 |
| osctiny/osc.py                      |      205 |       30 |     85% |146, 149-152, 206-212, 219, 223-229, 331-338, 350, 464, 470, 497, 513 |
| osctiny/utils/\_\_init\_\_.py       |        0 |        0 |    100% |           |
| osctiny/utils/auth.py               |      118 |       33 |     72% |28, 42, 83-93, 128, 131, 137, 152-170, 189-190, 200, 214-215, 220, 227 |
| osctiny/utils/backports.py          |       11 |        7 |     36% |10-18, 24-26 |
| osctiny/utils/base.py               |       35 |        4 |     89% |     59-63 |
| osctiny/utils/changelog.py          |       95 |        6 |     94% |64, 75, 93, 104, 161, 271 |
| osctiny/utils/conf.py               |       73 |       24 |     67% |20, 66, 107, 129-149, 178, 181-186, 189 |
| osctiny/utils/errors.py             |        1 |        0 |    100% |           |
| osctiny/utils/mapping.py            |       37 |       10 |     73% |29, 32, 35, 38, 44, 47, 56, 59, 72-73 |
| setup.py                            |       15 |       15 |      0% |      3-27 |
|                           **TOTAL** | **1190** |  **291** | **76%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/crazyscientist/osc-tiny/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/crazyscientist/osc-tiny/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/crazyscientist/osc-tiny/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/crazyscientist/osc-tiny/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fcrazyscientist%2Fosc-tiny%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/crazyscientist/osc-tiny/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.