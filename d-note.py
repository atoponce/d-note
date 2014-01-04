#!/usr/bin/python
# -*- coding: utf-8 -*-
import base64
import glob
import os
import time
import zlib
from Crypto import Random
from Crypto.Cipher import Blowfish
from flask import Flask, render_template, request, redirect, url_for
from threading import Thread

dnote = Flask(__name__)

# CHANGEME. Should be at least 16 bytes long.
# strings /dev/urandom | grep -o '[[:alnum:]]' | head -n 16 | tr -d 'n'; echo
key = "cN7RPiuMhJwX1e9MUwuTXggpK9r2ym"

def async(func):
    """Return threaded wrapper function."""
    dnote.logger.debug('async decorator')
    def wrapper(*args, **kwargs):
        t = Thread(target = func, args = args, kwargs = kwargs)
        t.start()
    return wrapper

@async
def note_destroy():
    """Destroy unread notes older than 30 days."""
    dnote.logger.debug('note_destroy')
    while True:
        start_time = time.time()
        for f in os.listdir('data/'):
            file_mtime = os.stat(f)[8]
            if (start_time - file_mtime) > 2592000:
                secure_remove(f)
        time.sleep(86400)

def secure_remove(path):
    """Securely overwrite any file, then remove the file.

    Do not make any assumptions about the underlying filesystem, whether
    it's journaled, copy-on-write, or whatever.

    Keyword arguments:
    path -- an absolute path to the file to overwrite with random data
    """
    dnote.logger.debug('secure_remove')
    r = Random.new()
    with open(path, "r+") as f:
        for char in xrange(os.stat(f.name).st_size):
            f.seek(char)
            f.write(chr(r.read(1)))
    os.remove(path)

def note_encrypt(key, plaintext, new_url, key_file):
    """Encrypt a plaintext to a URI file.

    All files are encrypted with Blowfish in ECB mode. Plaintext is
    compressed with ZLIB first before encryption to prevent leaking
    repeated blocks in the ciphertext. Also saves disk space.

    Keyword arguments:
    key -- private key to encrypt the plaintext
    plaintext -- the message to be encrypted
    new_url -- file to save the encrypted text to
    key_file -- 'True' only if a private key was used for encryption
    """
    dnote.logger.debug('note_encrypt')
    pad = lambda s: s + (8 - len(s) % 8) * chr(8 - len(s) % 8)
    plain = pad(zlib.compress(plaintext.encode('utf-8')))
    if key_file:
        # create empty file with '.key' as an extension
        open('data/%s.key' % new_url, 'a').close()
    with open('data/%s' % new_url, 'w') as f:
        bf = Blowfish.new(key, Blowfish.MODE_ECB)
        ciphertext = bf.encrypt(plain)
        f.write(ciphertext.encode("base64"))

def note_decrypt(key, ciphertext):
    """Decrypt a ciphertext from a given URI file.

    Keyword arguments:
    key -- private key to decrypt the ciphertext
    ciphertext -- the message to be decrypted
    """
    dnote.logger.debug('note_decrypt')
    unpad = lambda s : s[0:-ord(s[-1])]
    with open('data/%s' % ciphertext, 'r') as f:
        message = f.read()
    bf = Blowfish.new(key, Blowfish.MODE_ECB)
    plaintext = bf.decrypt(message.decode("base64"))
    return zlib.decompress(unpad(plaintext)).decode('utf-8')

def create_url():
    """Return a new random 128-bit URI for retrieval."""
    dnote.logger.debug('create_url')
    new_url = base64.urlsafe_b64encode(Random.new().read(16))[:22]
    if os.path.exists('data/%s' % new_url):
        create_url()
    return new_url

@dnote.route('/', methods = ['POST','GET'])
def index():
    """Return the index.html for the main application."""
    dnote.logger.debug('default route')
    error = None
    new_url = create_url()
    return render_template('index.html', random = new_url, error=error)

@dnote.route('/post/<new_url>', methods = ['POST', 'GET'])
def show_post(new_url):
    """Return the random URL after posting the plaintext.
    
    Keyword arguments:
    new_url -- encrypted file representing the unique URL
    """
    if request.method == 'POST':
        plaintext = request.form['paste']
        if request.form['pass']:
            privkey = request.form['pass']
            key_file = True
            note_encrypt(privkey, plaintext, new_url, key_file)
        else:
            key_file = False
            note_encrypt(key, plaintext, new_url, key_file)
    else:
        error = "Invalid data."
    return render_template('post.html', random = new_url)

@async
@dnote.route('/<random_url>', methods = ['POST', 'GET'])
def fetch_url(random_url):
    """Return the decrypted note. Begin short destruction timer.
    
    Keyword arguments:
    random_url -- Random URL representing the encrypted note
    """
    if os.path.exists('data/%s.key' % random_url) and request.method != 'POST':
        return render_template('key.html', random = random_url)
    elif os.path.exists('data/%s.key' % random_url) and request.method == 'POST':
        privkey = request.form['pass']
        try:
            plaintext = note_decrypt(privkey, random_url)
            return render_template('note.html', text = plaintext)
        except:
            return render_template('keyerror.html', random=random_url)
    else:
        plaintext = note_decrypt(key, random_url)
        return render_template('note.html', text = plaintext)

if __name__ == '__main__':
    dnote.debug = True
    note_destroy()
    dnote.run()
