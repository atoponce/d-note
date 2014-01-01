import os
import base64
from Crypto.Cipher import Blowfish
from Crypto import Random
from flask import Flask, render_template, request

app = Flask(__name__)

key = Random.new().read(8)

def encrypt(plaintext, new_url):
    pad = lambda s: s + (8 - len(s) % 8) * chr(8 - len(s) % 8)
    f = open('data/%s' % new_url, w)
    plaintext = pad(plaintext)
    iv = Random.new().read(8)
    cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
    ciphertext = iv + cipher.encrypt(plaintext).encode("hex")
    f.write(ciphertext)
    f.close()
    return(ciphertext)

def decrypt(ciphertext):
    unpad = lambda s : s[0:-ord(s[-1])]
    f = open('data/%s' % ciphertext, r)
    iv = f[:8]
    message = f[8:]
    message = message.decode("hex")
    cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
    close(f)
    return unpad(cipher.decrypt(message))

def create_url():
    new_url = base64.urlsafe_b64encode(os.urandom(16))
    if os.path.exists('data/%s' % new_url):
        create_url()
    
@app.route('/', methods = ['POST','GET'])
def index():
    new_url = create_url()
    if request.method == 'POST':
        plaintext = request.form['paste']
        ciphertext = encrypt(plaintext, new_url)
        show_post(new_url)
    return render_template('index.html', random = new_url)

@app.route('/post/<new_url>', methods = ['POST', 'GET'])
def show_post(new_url):
    return render_template('post.html', random = new_url)

@app.route('/<random_url>')
def fetch_url(random_url):
    plaintext = decrypt(random_url)
    return render_template('note.html', text = plaintext)

if __name__ == '__main__':
    app.debug = True
    app.run()
