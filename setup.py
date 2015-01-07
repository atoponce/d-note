#!/usr/bin/env python

from setuptools import setup

import os
import glob

DCONFIG = os.path.dirname(os.path.realpath(__file__)) + "/dnote/dconfig.py"

if not os.path.exists(DCONFIG):
    with open(DCONFIG, 'w') as f:
        f.write('aes_salt = "%s"\n' % os.urandom(16).encode('hex'))
        f.write('mac_salt = "%s"\n' % os.urandom(16).encode('hex'))
        f.write('nonce_salt = "%s"\n' % os.urandom(16).encode('hex'))
        f.write('duress_salt = "%s"\n' % os.urandom(16).encode('hex'))
    os.chmod(DCONFIG, 0440)

setup(
    name='dnote',
    version='1.0.1',
    description='Self-destructing notes web app',
    license='GPLv3',
    author='Aaron Toponce',
    author_email='aaron.toponce@gmail.com',
    url='http://github.com/atoponce/d-note/',
    packages=['dnote'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask'],
)
