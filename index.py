import os
import base64
from Crypto.Cipher import Blowfish
from Crypto import Random
from flask import Flask, render_template, request

app = Flask(__name__)

# Change me.
key = "cN7RPiuMhJwX1e9MUwuTXggpK9r2ym"

def encrypt(key, plaintext, new_url):
    pad = lambda s: s + (8 - len(s) % 8) * chr(8 - len(s) % 8)
    f = open('data/%s' % new_url, 'w')
    plaintext = pad(f)
    iv = Random.new().read(8)
    cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
    ciphertext = iv + cipher.encrypt(plaintext).encode("base64")
    f.write(ciphertext)
    f.close()
    return(ciphertext)

def decrypt(ciphertext):
    unpad = lambda s : s[0:-ord(s[-1])]
    f = open('data/%s' % ciphertext, 'r')
    iv = f[:8]
    message = f[8:]
    close(f)
    message = message.decode("base64")
    cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
    return unpad(cipher.decrypt(message))

def create_url():
    new_url = base64.urlsafe_b64encode(Random.new().read(16))[:22]
    if os.path.exists('data/%s' % new_url):
        create_url()
    return new_url
    
@app.route('/', methods = ['POST','GET'])
def index():
    new_url = create_url()
    error = None
    if request.method == 'POST':
        if request.form['pass']:
            key = request.form['pass']
        plaintext = request.form['paste']
        ciphertext = encrypt(key, plaintext, new_url)
        show_post(new_url)
    else:
        error = "Invalid data."
    return render_template('index.html', random = new_url, error=error)

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
