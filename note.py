"""Encrypts and decrypts notes."""
import base64
import os
import zlib
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA512
from Crypto.Protocol import KDF
from Crypto.Random import random
from Crypto.Util import Counter

try:
    import dconfig
except ImportError:
    with open('dconfig.py', 'w') as f:
        f.write('aes_salt = "%s"\n' % Random.new().read(16).encode('hex'))
        f.write('mac_salt = "%s"\n' % Random.new().read(16).encode('hex'))
        f.write('nonce_salt = "%s"\n' % Random.new().read(16).encode('hex'))
        f.write('duress_salt = "%s"\n' % Random.new().read(16).encode('hex'))
    import dconfig

DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class Note(object):
    """Note Model"""
    url = None          # URI of Note
    nonce = None        # ID decoded from url
    fname = None        # File name
    f_key = None        # ID decoded from fname
    aes_key = None      # AES encryption key
    mac_key = None      # HMAC verification key
    passphrase = None   # User provided passphrase
    dkey = None         # Duress passphrase
    plaintext = None    # Plain text note
    ciphertext = None   # Encrypted text

    def __init__(self, url=None):
        if url is None:
            self.create_url()
        else:
            self.decode_url(url)

    def exists(self):
        """Checks if note already exists"""
        return os.path.exists(self.path())

    def path(self, kind=None):
        """Return the file path to the note file"""
        if kind is None:
            return '%s/%s' % (DATA_DIR, self.fname)
        else:
            return '%s/%s.%s' % (DATA_DIR, self.fname, kind)

    def create_url(self):
        """Create a cryptographic nonce for our URL, and use PBKDF2 with our
        nonce and our salts to generate a file name, AES key, and MAC key.

            - 128-bits for the URL
            - 128-bits for file name
            - 256-bits for AES-256 key
            - 512-bits for HMAC-SHA512 key"""

        self.nonce = Random.new().read(16)
        self.f_key = KDF.PBKDF2(
            self.nonce, dconfig.nonce_salt.decode("hex"), 16)
        self.aes_key = KDF.PBKDF2(
            self.nonce, dconfig.aes_salt.decode("hex"), 32)
        self.mac_key = KDF.PBKDF2(
            self.nonce, dconfig.mac_salt.decode("hex"), 64)
        self.url = base64.urlsafe_b64encode(self.nonce)[:22]
        self.fname = base64.urlsafe_b64encode(self.f_key)[:22]
        if self.exists():
            return self.create_url()

    def decode_url(self, url):
        """Takes a URL, and returns the cryptographic nonce. Use PBKDF2 with our
        nonce and our salts to return the file name, AES key, and MAC key.

        keyword arguments:
        url -- the url after the FQDN provided by the client"""

        self.url = url
        url = url + "==" # add the padding back
        self.nonce = base64.urlsafe_b64decode(url.encode("utf-8"))
        self.f_key = KDF.PBKDF2(
            self.nonce, dconfig.nonce_salt.decode("hex"), 16)
        self.aes_key = KDF.PBKDF2(
            self.nonce, dconfig.aes_salt.decode("hex"), 32)
        self.mac_key = KDF.PBKDF2(
            self.nonce, dconfig.mac_salt.decode("hex"), 64)
        duress = KDF.PBKDF2(
            self.nonce, dconfig.duress_salt.decode("hex"), 16)
        self.dkey = base64.urlsafe_b64encode(duress)[:22]
        self.fname = base64.urlsafe_b64encode(self.f_key)[:22]

    def set_passphrase(self, passphrase):
        """Set a user defined passphrase to override the AES and HMAC keys"""
        self.passphrase = passphrase
        self.aes_key = KDF.PBKDF2(
            passphrase, dconfig.aes_salt.decode("hex"), 32)
        self.mac_key = KDF.PBKDF2(
            passphrase, dconfig.mac_salt.decode("hex"), 64)

    def duress_key(self):
        """Generates a duress key for Big Brother. It is stored on disk in
        plaintext."""
        duress_key = KDF.PBKDF2(
            self.nonce, dconfig.duress_salt.decode('hex'), 16)
        self.dkey = base64.urlsafe_b64encode(duress_key)[:22]

    def secure_remove(self):
        """Securely overwrite any file, then remove the file. Do not make any
        assumptions about the underlying filesystem, whether it's journaled,
        copy-on-write, or whatever."""

        rand = Random.new()
        for kind in (None, 'key', 'dkey'):
            if not os.path.exists(self.path(kind)): continue
            with open(self.path(kind), "r+") as note:
                for char in xrange(os.stat(note.name).st_size):
                    note.seek(char)
                    note.write(str(rand.read(1)))
            os.remove(self.path(kind))

    def encrypt(self):
        """Encrypt a plaintext to a URI file.

        All files are encrypted with AES in CTR mode. HMAC-SHA512 is used
        to provide authenticated encryption ( encrypt then mac ). No private keys
        are stored on the server."""
        
        plain = zlib.compress(self.plaintext.encode('utf-8')) 
        with open(self.path(), 'w') as note:
            init_value = Random.new().read(12) # 96-bits
            ctr = Counter.new(128, initial_value = long(init_value.encode('hex'), 16))
            aes = AES.new(self.aes_key, AES.MODE_CTR, counter = ctr)
            ciphertext = aes.encrypt(plain)
            ciphertext = init_value + ciphertext
            hmac = HMAC.new(self.mac_key, ciphertext, SHA512)
            ciphertext = hmac.digest() + ciphertext
            note.write(ciphertext)

    def decrypt(self):
        """Decrypt the ciphertext from a given URI file."""

        with open(self.path(), 'r') as note:
            message = note.read()
        tag = message[:64]
        data = message[64:]
        init_value = data[:12]
        body = data[12:]
        ctr = Counter.new(128, initial_value=long(init_value.encode('hex'), 16))
        aes = AES.new(self.aes_key, AES.MODE_CTR, counter=ctr)
        plaintext = aes.decrypt(body)
        # check the message tags, return True if is good
        # constant time comparison
        tag2 = HMAC.new(self.mac_key, data, SHA512).digest()
        hmac_check = 0
        for char1, char2 in zip(tag, tag2):
            hmac_check |= ord(char1) ^ ord(char2)
        if hmac_check == 0:
            self.plaintext = zlib.decompress(plaintext).decode('utf-8')
        else: 
            return False
        return True
