import base64
import os
import zlib
from Crypto import Random
from Crypto.Cipher import Blowfish
from flask import Flask, render_template, request
from threading import Thread

dnote = Flask(__name__)

# CHANGEME. Should be at least 16 bytes long.
# strings /dev/urandom | grep -o '[[:alnum:]]' | head -n 16 | tr -d 'n'; echo
key = "cN7RPiuMhJwX1e9MUwuTXggpK9r2ym"

def async(func):
    def wrap(*args, **kwargs):
        t = Thread(target = func, args = args, kwargs = kwargs)
        t.start()
    return wrap

@async
def note_destroy()
    while True:
        # code to identify which files to destroy

def note_encrypt(key, plaintext, new_url):
    dnote.logger.debug('note_encrypt')
    pad = lambda s: s + (8 - len(s) % 8) * chr(8 - len(s) % 8)
    plain = pad(zlib.compress(plaintext))
    with open('data/%s' % new_url, 'w') as f:
        bf = Blowfish.new(key, Blowfish.MODE_ECB)
        ciphertext = bf.encrypt(plain)
        f.write(ciphertext.encode("base64"))

def note_decrypt(ciphertext):
    dnote.logger.debug('note_decrypt')
    unpad = lambda s : s[0:-ord(s[-1])]
    with open('data/%s' % ciphertext, 'r') as f:
        message = f.read()
    bf = Blowfish.new(key, Blowfish.MODE_ECB)
    plaintext = bf.decrypt(message.decode("base64"))
    return zlib.decompress(unpad(plaintext))

def create_url():
    dnote.logger.debug('create_url')
    new_url = base64.urlsafe_b64encode(Random.new().read(16))[:22]
    if os.path.exists('data/%s' % new_url):
        create_url()
    return new_url
    
@dnote.route('/', methods = ['POST','GET'])
def index():
    dnote.logger.debug('default route')
    error = None
    new_url = create_url()
    return render_template('index.html', random = new_url, error=error)

@dnote.route('/post/<new_url>', methods = ['POST', 'GET'])
def show_post(new_url):
    if request.method == 'POST':
        dnote.logger.debug('handle post request')
        plaintext = request.form['paste']
        dnote.logger.debug('create cipher file')
        note_encrypt(key, plaintext, new_url)
    else:
        error = "Invalid data."
    return render_template('post.html', random = new_url)

@dnote.route('/<random_url>')
def fetch_url(random_url):
    plaintext = note_decrypt(random_url)
    return render_template('note.html', text = plaintext)

if __name__ == '__main__':
    dnote.debug = True
    note_destroy()
    dnote.run()
