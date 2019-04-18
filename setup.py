#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open("README.md") as fh:
    long_description = fh.read()


setup(
    name='osc-tiny',
    version='0.1.1',
    description='Library for read-only access to the openSUSE BuildService',
    long_description=long_description,
    long_description_content_type="text/markdown",
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
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ]
)
