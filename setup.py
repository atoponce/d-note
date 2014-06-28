#!/usr/bin/python

import os
from Crypto import Random

DCONFIG = os.path.dirname(os.path.realpath(__file__)) + "/dconfig.py"
DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data"

if not os.path.exists(DCONFIG):
    with open('dconfig.py', 'w') as f:
        f.write('aes_salt = "%s"\n' % Random.new().read(16).encode('hex'))
        f.write('mac_salt = "%s"\n' % Random.new().read(16).encode('hex'))
        f.write('nonce_salt = "%s"\n' % Random.new().read(16).encode('hex'))
        f.write('duress_salt = "%s"\n' % Random.new().read(16).encode('hex'))
    os.chmod('dconfig.py',0440)

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
