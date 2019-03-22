#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='osc-tiny',
    version='0.0.0',
    description='Library for accessing the openSUSE BuildService',
    long_description='osc-tiny provides rudimentary API access',
    author='Andreas Hasenkopf',
    author_email='ahasenkopf@suse.com',
    url='http://github.com/crazyscientist/osc-tiny',
    download_url='http://github.com/crazyscientist/osc-tiny/tarball/master',
    packages=find_packages(),
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
    ]
)
