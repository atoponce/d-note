import base64
import os
import zlib
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA, SHA512
from Crypto.Protocol import KDF
from Crypto.Random import random
from Crypto.Util import Counter

try:
    import dconfig
except ImportError:
    with open('dconfig.py','w') as f:
        f.write('aes_salt = "{0}"\n'.format(Random.new().read(16).encode('hex')))
        f.write('mac_salt = "{0}"\n'.format(Random.new().read(16).encode('hex')))
        f.write('nonce_salt = "{0}"\n'.format(Random.new().read(16).encode('hex')))
    import dconfig

here = os.path.dirname(os.path.realpath(__file__))

class Note(object):
    """Note Model"""
    url = None      # URI of Note
    nonce = None    # ID decoded from url
    fname = None    # File name
    f_key = None    # ID decoded from fname
    aes_key = None  # AES encryption key
    mac_key = None  # HMAC verification key
    passphrase = None   # User provided passphrase
    dkey = None     # Duress passphrase
    plaintext = None    # Plain text note
    ciphertext = None   # Encrypted text

    def __init__(self,url=None):
        if url is None:
            self.create_url()
        else:
            self.decode_url(url)

    def path(self,kind=None):
        """Return the file path to the note file"""
        if kind is None:
            return '%s/data/%s' % (here, self.fname)
        else:
            return '%s/data/%s.%s' % (here, self.fname, kind)

    def create_url(self):
        """Create a cryptographic nonce for our URL, and use PBKDF2 with our nonce
        and our salts to generate a file name, AES key, and MAC key.
    
            - 128-bits for the URL
            - 128-bits for file name
            - 256-bits for AES-256 key
            - 512-bits for HMAC-SHA512 key"""
    
        self.nonce = Random.new().read(16)
        self.f_key = KDF.PBKDF2(self.nonce,dconfig.nonce_salt.decode("hex"),16)
        self.aes_key = KDF.PBKDF2(self.nonce,dconfig.aes_salt.decode("hex"),32)
        self.mac_key = KDF.PBKDF2(self.nonce,dconfig.mac_salt.decode("hex"),64)
        self.url = base64.urlsafe_b64encode(self.nonce)[:22] # remove trailing '==' from url
        self.fname = base64.urlsafe_b64encode(self.f_key)[:22]
        if os.path.exists(self.path()):
            return self.create_url()
    
    def decode_url(self,url):
        """Takes a URL, and returns the cryptographic nonce. Use PBKDF2 with our
        nonce and our salts to return the file name, AES key, and MAC key.
    
        keyword arguments:
        url -- the url after the FQDN provided by the client"""
    
        self.url = url
        url = url + "==" # add the padding back
        self.nonce = base64.urlsafe_b64decode(url.encode("utf-8"))
        self.f_key = KDF.PBKDF2(self.nonce,dconfig.nonce_salt.decode("hex"),16)
        self.aes_key = KDF.PBKDF2(self.nonce,dconfig.aes_salt.decode("hex"),32)
        self.mac_key = KDF.PBKDF2(self.nonce,dconfig.mac_salt.decode("hex"),64)
        self.fname = base64.urlsafe_b64encode(self.f_key)[:22]
        if os.path.exists(self.path('dkey')):
            with open(self.path('dkey'), 'r') as f:
                self.dkey = f.read()

    def set_passphrase(self,passphrase):
        """Set a user defined passphrase to override the AES and HMAC keys"""
        self.passphrase = passphrase
        self.aes_key = KDF.PBKDF2(passphrase, dconfig.aes_salt.decode("hex"), 32)
        self.mac_key = KDF.PBKDF2(passphrase, dconfig.mac_salt.decode("hex"), 64)

    def duress_key(self):
        """Generates a duress key for Big Brother. It is stored on disk in plaintext."""
    
        import string
        chars = string.ascii_letters + string.digits
        self.dkey = ''.join(random.choice(chars) for i in xrange(24))
        with open(self.path('dkey'), 'w') as f:
            f.write(self.dkey)

    def secure_remove(self):
        """Securely overwrite any file, then remove the file. Do not make any
        assumptions about the underlying filesystem, whether it's journaled,
        copy-on-write, or whatever."""
    
        r = Random.new()
        for kind in (None,'key','dkey'):
            if not os.path.exists(self.path(kind)): continue
            with open(self.path(kind), "r+") as f:
                for char in xrange(os.stat(f.name).st_size):
                    f.seek(char)
                    f.write(str(r.read(1)))
            os.remove(self.path(kind))

    def encrypt(self):
        """Encrypt a plaintext to a URI file.
    
        All files are encrypted with AES in CTR mode. HMAC-SHA512 is used
        to provide authenticated encryption ( encrypt then mac ). No private keys
        are stored on the server."""
    
        plain = zlib.compress(self.plaintext.encode('utf-8'))
        if self.passphrase is not None:
            open(self.path('key'), 'a').close() # empty file
    
        with open(self.path(), 'w') as f:
            iv = Random.new().read(12) # 96-bits
            ctr = Counter.new(128, initial_value = long(iv.encode('hex'), 16))
            aes = AES.new(self.aes_key, AES.MODE_CTR, counter = ctr)
            ciphertext = aes.encrypt(plain)
            ciphertext = iv + ciphertext
            hmac = HMAC.new(self.mac_key,ciphertext,SHA512) # generate a hmac tag
            ciphertext = hmac.digest() + ciphertext
            f.write(ciphertext)
            self.ciphertext = ciphertext
    
    def decrypt(self):
        """Decrypt the ciphertext from a given URI file."""
    
        with open(self.path(), 'r') as f:
            message = f.read()
        tag = message[:64]
        data = message[64:]
        iv = data[:12]
        body = data[12:]
        ctr = Counter.new(128, initial_value = long(iv.encode('hex'), 16))
        aes = AES.new(self.aes_key, AES.MODE_CTR, counter = ctr)
        plaintext = aes.decrypt(body)
        try:
            self.plaintext = zlib.decompress(plaintext).decode('utf-8')
        except zlib.error:
            return False
        # check the message tags, return 0 if is good
        # constant time comparison
        tag2 = HMAC.new(self.mac_key,data,SHA512).digest()
        hmac_check = 0
        for x, y in zip(tag, tag2):
            hmac_check |= ord(x) ^ ord(y)

        if hmac_check == 0:
            return True
        else:
            return False

