#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from setuptools import setup


setup(name='osc-tiny',
      description='Library for accessing the openSUSE BuildService',
      long_description='osc-tiny provides rudimentary API access',
      author='Andreas Hasenkopf',
      author_email='ahasenkopf@suse.com',
      url='http://github.com/crazyscientist/osc-tiny',
      download_url='http://github.com/crazyscientist/osc-tiny/tarball/master',
      packages=[

      ],
      # package_data={'osc2': ['cli/*.jinja2', 'cli/*/*.jinja2']},
      # scripts=['scripts/osc2'],
      # test_suite='test.suite',
      # entry_points={'console_scripts': ['osc2 = osc2.cli.cli:main']},
      license='MIT',
      install_requires=[
          "lxml",
          "requests",
          "responses"
      ],
      classifiers=[
          "Intended Audience :: Developers",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Programming Language :: Python :: 3 :: Only"
      ])
