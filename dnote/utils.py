"""Utility functions for d-note."""
import random
from Crypto.Hash import SHA
from note import data_dir

def duress_text():
    """Return 5 random sentences of the Zen of Python."""
    import subprocess
    text = ''
    python = subprocess.Popen(('python', '-c', 'import this'),
                              stdout=subprocess.PIPE)
    sentence = [x for x in python.communicate()[0].splitlines() if x != '']
    for _ in range(5):
        text = text + random.choice(sentence) + ' '
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

    digest = SHA.new(token)
    with open('%s/hashcash.db' % data_dir, 'a+') as database:
        if digest.hexdigest()[:4] == '0000' and token not in database.read():
            database.write(token+'\n')
            return True
        else:
            return False
