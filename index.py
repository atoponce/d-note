import os
import base64
from Crypto.Cipher import Blowfish
from Crypto import Random
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Change me. Should be at least 16 bytes long.
# strings /dev/urandom | grep -o '[[:alnum:]]' | head -n 16 | tr -d 'n'; echo
key = "cN7RPiuMhJwX1e9MUwuTXggpK9r2ym"

def note_encrypt(key, plaintext, new_url):
    pad = lambda s: s + (8 - len(s) % 8) * chr(8 - len(s) % 8)
    with open('data/%s' % new_url, 'w') as f:
        plaintext = pad(plaintext)
        cipher = Blowfish.new(key, Blowfish.MODE_ECB)
        ciphertext = cipher.encrypt(plaintext).encode("base64")
        f.write(ciphertext)

    return(ciphertext)

def note_decrypt(ciphertext):
    unpad = lambda s : s[0:-ord(s[-1])]
    with open('data/%s' % ciphertext, 'r') as f:
        message = f.read()
    message = message.decode("base64")
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    return unpad(cipher.decrypt(message))

def create_url():
    new_url = base64.urlsafe_b64encode(Random.new().read(16))[:22]
    if os.path.exists('data/%s' % new_url):
        create_url()
    return new_url
    
@app.route('/', methods = ['POST','GET'])
def index():
    error = None
    new_url = create_url()
    return render_template('index.html', random = new_url, error=error)

@app.route('/post/<new_url>', methods = ['POST', 'GET'])
def show_post(new_url):
    if request.method == 'POST':
        plaintext = request.form['paste']
        ciphertext = note_encrypt(key, plaintext, new_url)
        #return redirect(url_for('fetch_url', random_url=new_url))
    else:
        error = "Invalid data."
    return render_template('post.html', random = new_url)

@app.route('/<random_url>')
def fetch_url(random_url):
    plaintext = note_decrypt(random_url)
    return render_template('note.html', text = plaintext)

if __name__ == '__main__':
    #app.debug = True
    app.run()
