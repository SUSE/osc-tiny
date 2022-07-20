#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sys import version_info
from setuptools import setup, find_packages


def get_requires():
    requirements = []

    def _filter(requires):
        return [req.strip() for req in requires if req.strip()]

    with open("requirements.txt", "r") as fh:
        requirements += _filter(fh.readlines())

    if version_info.minor < 8:
        with open("requirements_pre38.txt", "r") as fh:
            requirements += _filter(fh.readlines())

    return requirements


with open("README.md") as fh:
    long_description = fh.read()


setup(
    name='osc-tiny',
    version='0.6.5',
    description='Client API for openSUSE BuildService',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Andreas Hasenkopf',
    author_email='ahasenkopf@suse.com',
    url='http://github.com/crazyscientist/osc-tiny',
    download_url='http://github.com/crazyscientist/osc-tiny/tarball/master',
    packages=find_packages(),
    license='MIT',
    install_requires=get_requires(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ]
)
