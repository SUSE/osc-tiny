# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/SUSE/osc-tiny/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                |    Stmts |     Miss |   Cover |   Missing |
|------------------------------------ | -------: | -------: | ------: | --------: |
| auto\_release\_obs.py               |       74 |       74 |      0% |     5-137 |
| osctiny/\_\_init\_\_.py             |        4 |        0 |    100% |           |
| osctiny/extensions/\_\_init\_\_.py  |        0 |        0 |    100% |           |
| osctiny/extensions/attributes.py    |       20 |        0 |    100% |           |
| osctiny/extensions/bs\_requests.py  |       47 |        1 |     98% |        26 |
| osctiny/extensions/buildresults.py  |       36 |       19 |     47% |62-69, 85-91, 105-112, 126-134, 150-158, 182-189, 209, 228-239 |
| osctiny/extensions/comments.py      |       34 |        4 |     88% |20, 28, 85, 98 |
| osctiny/extensions/distributions.py |       13 |        0 |    100% |           |
| osctiny/extensions/issues.py        |       26 |        0 |    100% |           |
| osctiny/extensions/origin.py        |      182 |       78 |     57% |37-39, 55-69, 77, 121-122, 130-146, 175, 177, 181, 189, 249-251, 262-265, 285-286, 288, 417, 442-450, 463-467, 490-520, 530-542 |
| osctiny/extensions/packages.py      |      139 |       41 |     71% |73-80, 217-227, 256, 306-322, 334-347, 412, 427, 452-460, 484-500, 579-583, 603, 606, 627, 646 |
| osctiny/extensions/projects.py      |      115 |       17 |     85% |92-94, 172, 197, 200, 257, 278, 304, 317, 337, 358-371, 420, 451 |
| osctiny/extensions/search.py        |       13 |        1 |     92% |        56 |
| osctiny/extensions/staging.py       |       95 |        8 |     92% |82, 104, 167, 211, 237, 313, 370, 383 |
| osctiny/extensions/users.py         |       18 |        9 |     50% |23-32, 42-47, 65-70 |
| osctiny/models/\_\_init\_\_.py      |        6 |        0 |    100% |           |
| osctiny/models/request.py           |       52 |        0 |    100% |           |
| osctiny/models/staging.py           |       44 |        4 |     91% |     56-62 |
| osctiny/osc.py                      |      168 |       19 |     89% |158, 161-164, 208, 212-220, 230, 304-305, 311, 431, 437 |
| osctiny/utils/\_\_init\_\_.py       |        0 |        0 |    100% |           |
| osctiny/utils/auth.py               |      118 |       36 |     69% |35, 70-86, 113-121, 156, 159, 165, 180-190, 209-210, 220, 234-235, 240, 247 |
| osctiny/utils/backports.py          |        4 |        2 |     50% |     14-16 |
| osctiny/utils/base.py               |        3 |        0 |    100% |           |
| osctiny/utils/changelog.py          |       96 |        6 |     94% |69, 80, 98, 109, 167, 277 |
| osctiny/utils/conf.py               |       73 |       24 |     67% |21, 67, 108, 130-150, 179, 182-187, 190 |
| osctiny/utils/cookies.py            |       37 |        7 |     81% |     25-35 |
| osctiny/utils/errors.py             |       19 |        1 |     95% |        24 |
| osctiny/utils/mapping.py            |       37 |       10 |     73% |29, 32, 35, 38, 44, 47, 56, 59, 72-73 |
| osctiny/utils/session.py            |       37 |        2 |     95% |    55, 64 |
| osctiny/utils/xml.py                |       24 |        2 |     92% |    62, 78 |
| setup.py                            |       15 |       15 |      0% |      3-27 |
|                           **TOTAL** | **1549** |  **380** | **75%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/SUSE/osc-tiny/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/SUSE/osc-tiny/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/SUSE/osc-tiny/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/SUSE/osc-tiny/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FSUSE%2Fosc-tiny%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/SUSE/osc-tiny/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.