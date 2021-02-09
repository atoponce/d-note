#!/usr/bin/env python3

from setuptools import setup, find_packages

import os
import glob


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='dnote',
    version='2.0.0',
    description='d-note is a self-destructing notes web application',
    packages=find_packages(),
    install_requires=['Flask', 'pycrypto', 'uwsgi'],
    zip_safe=False,
    include_package_data=True,
    license='GPLv3',
    author_email='aaron.toponce@gmail.com',
    author='Aaron Toponce',
    maintainer='Jarrod Price',
    url='http://github.com/Pyroseza/d-note',
    long_description=read('README'),
    scripts=['scripts/generate_dnote_hashes'],
    data_files=[('/etc/dnote', ['d-note.ini']), ('/var/www/dnote', ['wsgi.py'])],
    python_requires='>=3.9',
)
