"""Utility functions for d-note."""
import codecs
import os
import random
from Crypto.Hash import SHA
from .note import data_dir


def dec(obj, encoding: str = 'hex'):
    return codecs.decode(obj, encoding)


def enc(obj, encoding: str = 'hex'):
    return codecs.encode(obj, encoding)


def get_rand_bytes(length: int = 16) -> bytes:
    return os.urandom(length)


def logit(name, var):
    print(f"var: {name}, value: {var}, type: {type(var)}")


def duress_text():
    """Return 5 random sentences of the Zen of Python."""
    import subprocess
    text = ''
    python = subprocess.Popen(('python3', '-c', 'import this'), stdout=subprocess.PIPE)
    lines = dec(python.communicate()[0], "utf-8").splitlines()
    sentence = [x for x in lines if x != '']
    text = ' '.join(random.choices(sentence, k=5))
    return text


def verify_hashcash(token):
    """Return True or False based on the Hashcash token

    Valid Hashcash tokens must start with '0000' in the SHA hexdigest string.
    If not, then return False to redirect the user to an error page. If the
    token is valid, but has already been spent, then also return False to
    redirect the user to an error page. Otherwise, if the token is valid and
    has not been spent, append it to the hashcash.db file.

    Keyword arguments:
    token -- a proposed Hashcash token to validate."""

    digest = SHA.new(enc(token, "utf-8"))
    with open(os.path.join(data_dir, 'hashcash.db'), 'a+') as database:
        if digest.hexdigest()[:4] == '0000' and token not in database.read():
            database.write(f'{token}\n')
            return True
        else:
            return False
