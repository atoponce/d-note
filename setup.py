#!/usr/bin/env python

from distutils.core import setup

import os
import glob

DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data"
DCONFIG = os.path.dirname(os.path.realpath(__file__)) + "/dnote/dconfig.py"

if not os.path.exists(DCONFIG):
    with open(DCONFIG, 'w') as f:
        f.write('aes_salt = "%s"\n' % os.urandom(16).encode('hex'))
        f.write('mac_salt = "%s"\n' % os.urandom(16).encode('hex'))
        f.write('nonce_salt = "%s"\n' % os.urandom(16).encode('hex'))
        f.write('duress_salt = "%s"\n' % os.urandom(16).encode('hex'))
    os.chmod(DCONFIG, 0440)

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

data_files = [
('share/dnote/static/css', filter(os.path.isfile, glob.glob('dnote/static/css/*.css'))),
('share/dnote/static/img', filter(os.path.isfile, glob.glob('dnote/static/img/*'))),
('share/dnote/static/js', filter(os.path.isfile, glob.glob('dnote/static/js/*.js'))),
('share/dnote/templates', filter(os.path.isfile, glob.glob('dnote/templates/*'))),
]

setup(name='dnote',
      version='1.0.1',
      description='Self-destructing notes web app',
      license='GPLv3',
      author='Aaron Toponce',
      author_email='aaron.toponce@gmail.com',
      url='http://github.com/atoponce/d-note/',
      packages=['dnote'],
      install_requires=[
        "pycrypto",
        "Flask",
      ],
      data_files=data_files,
     )
