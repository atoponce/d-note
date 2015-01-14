#!/usr/bin/env python

from setuptools import setup, find_packages

import os
import glob

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='dnote',
    version='1.0.1',
    description='d-note is a self-destructing notes web application',
    packages=find_packages(),
    install_requires=['Flask'],
    zip_safe=False,
    include_package_data=True,
    license='GPLv3',
    author_email='aaron.toponce@gmail.com',
    author='Aaron Toponce',
    maintainer='Clint Savage',
    url='http://github.com/atoponce/d-note',
    long_description=read('README'),
    scripts=['scripts/generate_dnote_hashes'],
)
