#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
    name = "srl",
    version = "0.1",
    packages = find_packages(exclude=["tests"]),
    author = "Tigran Saluev",
    author_email = "tigran@saluev.com",
    description = "Simple Regex Languge implementation",
    license = "MIT",
)
