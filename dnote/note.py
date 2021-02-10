"""Encrypts and decrypts notes."""
import base64
import codecs
import configparser
import os
import sys
import zlib
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA512
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util import Counter
from . import utils

# copy the config file from conf dir to either /etc/dnote or ~/.dnote,
# then run this script.

try:

    config = configparser.ConfigParser()

    for path in ['/etc/dnote', '~/.dnote']:
        expanded_path = os.path.join(os.path.expanduser(path), 'd-note.ini')
        if os.path.exists(expanded_path):
            try:
                config.read(expanded_path)
                print(f"Using config file: {expanded_path}")
                break
            except configparser.InterpolationSyntaxError as e:
                raise EOFError(f"Unable to parse configuration file properly: {e}")
    else:
        raise ValueError("Config file not found")

    cfgs = config.defaults()

    for section in config.sections():
        if section not in cfgs:
            cfgs[section] = {}

        for k, v in config.items(section):
            cfgs[section][k] = v

    dconfig_path = os.path.expanduser(cfgs.get('dnote', {}).get('config_path'))
    dconfig = os.path.join(dconfig_path, "dconfig.py")

    # add dconfig.py to the sys.path
    sys.path.append(dconfig_path)

except Exception as e:
    raise Exception(f"unable to load config: {e}")

try:
    import dconfig
except ImportError:
    print("You need to run 'generate_dnote_hashes' as part of the installation.")
    os.sys.exit(1)

data_dir = cfgs.get('dnote').get('data_dir')


def cleave_hash(hash: str, remove=True):
    """ Generic function that can either strip off trailing equals signs from a base64 encoded
    byte string or figures out how to put them back"""
    if remove:
        return hash.replace('=', '')
    else:
        # 3 goes to identify the right ending for the hash
        for i in range(3):
            padding = '=' * i
            try:
                tmp_hash = f"{hash}{padding}"
                tmp_b64dec = base64.urlsafe_b64decode(utils.enc(tmp_hash, "utf-8"))
                return tmp_hash
            except Exception as e:
                continue
        raise ValueError("The partial hash you passed in is not compatible with this function")


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
    ciphertext = None   # encrypted text
    byte_size = None    # Used to calculate the size of the URL and duress key

    def __init__(self, url=None):
        """initialise for Note object, url is optional"""
        # load the byte_size from the config
        self.byte_size = max(int(cfgs['dnote'].get('byte_size', 16)), 4)
        if url is None:
            self.create_url()
        else:
            self.decode_url(url)

    def exists(self):
        """Checks if note already exists"""
        return os.path.exists(self.path())

    def path(self, kind=None):
        """Return the file path to the note file"""
        if isinstance(self.fname, bytes):
            self.fname = utils.dec(self.fname, "utf-8")
        file_path = os.path.join(os.path.expanduser(data_dir), self.fname)
        if kind is None:
            return file_path
        else:
            return f'{file_path}.{kind}'

    def create_url(self):
        """Create a cryptographic nonce for our URL, and use PBKDF2 with our
        nonce and our salts to generate a file name, AES key, and MAC key.

            - 128-bits for the URL
            - 128-bits for file name
            - 256-bits for AES-256 key
            - 512-bits for HMAC-SHA512 key"""
        self.nonce = utils.get_rand_bytes(self.byte_size)
        self.fname_and_fkey()
        self.aes_and_mac(self.nonce)
        self.url = cleave_hash(utils.dec(base64.urlsafe_b64encode(self.nonce), "utf-8"))
        if self.exists():
            return self.create_url()

    def decode_url(self, url):
        """Takes a URL, and returns the cryptographic nonce. Use PBKDF2 with our
        nonce and our salts to return the file name, AES key, and MAC key.

        keyword arguments:
        url -- the url after the FQDN provided by the client"""
        self.url = url
        obj = cleave_hash(url, remove=False)
        self.nonce = base64.urlsafe_b64decode(utils.enc(obj, "utf-8"))
        self.fname_and_fkey()
        self.aes_and_mac(self.nonce)
        self.duress_key()

    def fname_and_fkey(self):
        """Set filename and f_key"""
        self.f_key = PBKDF2(self.nonce, utils.dec(dconfig.nonce_salt), 16)
        self.fname = cleave_hash(utils.dec(base64.urlsafe_b64encode(self.f_key), "utf-8"))

    def aes_and_mac(self, obj):
        """Set AES and HMAC keys"""
        self.aes_key = PBKDF2(obj, utils.dec(dconfig.aes_salt), 32)
        self.mac_key = PBKDF2(obj, utils.dec(dconfig.mac_salt), 64)

    def set_passphrase(self, passphrase):
        """Set a user defined passphrase to override the AES and HMAC keys"""
        self.passphrase = passphrase
        self.aes_and_mac(passphrase)

    def duress_key(self):
        """Generates a duress key for Big Brother. It is stored on disk in
        plaintext."""
        duress_key = PBKDF2(self.nonce, utils.dec(dconfig.duress_salt), self.byte_size)
        self.dkey = cleave_hash(utils.dec(base64.urlsafe_b64encode(duress_key), "utf-8"))

    def secure_remove(self):
        """Securely overwrite any file, then remove the file. Do not make any
        assumptions about the underlying filesystem, whether it's journaled,
        copy-on-write, or whatever."""

        for kind in (None, 'key', 'dkey'):
            if not os.path.exists(self.path(kind)):
                continue
            with open(self.path(kind), "r+b") as note:
                for byt_idx in range(os.stat(note.name).st_size):
                    note.seek(byt_idx)
                    note.write(utils.get_rand_bytes(1))
            os.remove(self.path(kind))

    def encrypt(self):
        """encrypt a plaintext to a URI file.

        All files are encrypted with AES in CTR mode. HMAC-SHA512 is used
        to provide authenticated encryption ( encrypt then mac ). No private
        keys are stored on the server."""

        plain = zlib.compress(utils.enc(self.plaintext, 'utf-8'))
        with open(self.path(), 'wb') as note:
            init_value = utils.get_rand_bytes(12)
            ctr = Counter.new(128, initial_value=int(utils.enc(init_value), 16))
            aes = AES.new(self.aes_key, AES.MODE_CTR, counter=ctr)
            ciphertext = aes.encrypt(plain)
            ciphertext_with_init = init_value + ciphertext
            hmac = HMAC.new(self.mac_key, ciphertext_with_init, SHA512)
            # ciphertext = hmac.digest() + ciphertext
            hmac_dig = hmac.digest()
            ciphertext_with_init_and_hmac = hmac_dig + ciphertext_with_init
            note.write(ciphertext_with_init_and_hmac)

    def decrypt(self):
        """decrypt the ciphertext from a given URI file."""

        with open(self.path(), 'rb') as note:
            message = note.read()
        tag = message[:64]
        data = message[64:]
        init_value = data[:12]
        body = data[12:]
        ctr = Counter.new(128, initial_value=int(utils.enc(init_value), 16))
        aes = AES.new(self.aes_key, AES.MODE_CTR, counter=ctr)
        plaintext = aes.decrypt(body)
        # check the message tags, return True if is good
        # constant time comparison
        tag2 = HMAC.new(self.mac_key, data, SHA512).digest()
        hmac_check = 0
        for byte1, byte2 in zip(tag, tag2):
            # hmac_check |= ord(char1) ^ ord(char2)
            hmac_check |= byte1 ^ byte2
        if hmac_check == 0:
            self.plaintext = utils.dec(zlib.decompress(plaintext), 'utf-8')
        else:
            return False
        return True
