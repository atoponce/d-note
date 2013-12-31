import os
import base64
from Crypto.Cipher import AES
from Crypto import Random
from flask import Flask, render_template, request

app = Flask(__name__)

key = Random.new().read(16)

def encrypt(raw):
    pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
    plaintext = pad(raw)
    iv = Random.new().read(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return(iv + cipher.encrypt(raw)).encode("hex")

def decrypt(raw):
    unpad = lambda s : s[0:-ord(s[-1])]
    iv = raw[:16]
    raw = raw[16:]
    ciphertext = raw.decode("hex")
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(raw))

def create_file(u):
    encrypt(u)

def create_url():
    u = base64.urlsafe_b64encode(os.urandom(16))
    make_dir(u)
    return u

@app.route('/', methods=['POST'])
def index():
    error = None
    if request.method == 'POST':
        u = create_url()
        p = request.form['paste']
    else:
        error = 'Nothing submitted.'
    return render_template('index.html', error=error)

@app.route('/<random_url>')
def fetch_url(random_url):
    pass

if __name__ == '__main__':
    app.run(debug=True)
