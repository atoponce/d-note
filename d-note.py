import os
import zlib
import base64
from Crypto import Random
from Crypto.Cipher import Blowfish
from flask import Flask, render_template, request

app = Flask(__name__)

# Change me. Should be at least 16 bytes long.
# strings /dev/urandom | grep -o '[[:alnum:]]' | head -n 16 | tr -d 'n'; echo
key = "cN7RPiuMhJwX1e9MUwuTXggpK9r2ym"

def note_encrypt(key, plaintext, new_url):
    app.logger.debug('note_encrypt')
    pad = lambda s: s + (8 - len(s) % 8) * chr(8 - len(s) % 8)
    plain = pad(zlib.compress(plaintext))
    with open('data/%s' % new_url, 'w') as f:
        cipher = Blowfish.new(key, Blowfish.MODE_ECB)
        ciphertext = cipher.encrypt(plain)
        f.write(ciphertext.encode("base64"))

def note_decrypt(ciphertext):
    app.logger.debug('note_decrypt')
    unpad = lambda s : s[0:-ord(s[-1])]
    with open('data/%s' % ciphertext, 'r') as f:
        message = f.read()
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    plaintext = cipher.decrypt(message.decode("base64"))
    return zlib.decompress(unpad(plaintext))

def create_url():
    app.logger.debug('create_url')
    new_url = base64.urlsafe_b64encode(Random.new().read(16))[:22]
    if os.path.exists('data/%s' % new_url):
        create_url()
    return new_url
    
@app.route('/', methods = ['POST','GET'])
def index():
    app.logger.debug('default route')
    error = None
    new_url = create_url()
    return render_template('index.html', random = new_url, error=error)

@app.route('/post/<new_url>', methods = ['POST', 'GET'])
def show_post(new_url):
    if request.method == 'POST':
        app.logger.debug('handle post request')
        plaintext = request.form['paste']
        app.logger.debug('create cipher file')
        note_encrypt(key, plaintext, new_url)
    else:
        error = "Invalid data."
    return render_template('post.html', random = new_url)

@app.route('/<random_url>')
def fetch_url(random_url):
    plaintext = note_decrypt(random_url)
    return render_template('note.html', text = plaintext)

if __name__ == '__main__':
    app.debug = True
    app.run()
