import base64
import email.utils
import os
import smtplib
import time
import zlib
from Crypto import Random
from Crypto.Cipher import Blowfish
from Crypto.Hash import SHA
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for
from threading import Thread

# BEGIN CHANGEME.
key = "cN7RPiuMhJwX1e9MUwuTXggpK9r2ym" # Should be at least 16 bytes long.
fromaddr = "no-reply@example.com"
fullname = "John Doe"
# END CHANGEME.

dnote = Flask(__name__)
here = dnote.root_path

def send_email(link, recipient):
    """Send the link via email to a recipient."""
    msg = MIMEText("%s" % link)
    msg['To'] = email.utils.formataddr(('Self Destructing Notes', recipient))
    msg['From'] = email.utils.formataddr((fullname, fromaddr))
    s = smtplib.SMTP('localhost')
    s.sendmail(fromaddr, [recipient], msg.as_string())
    s.quit()
    
def async(func):
    """Return threaded wrapper decorator."""
    def wrapper(*args, **kwargs):
        t = Thread(target = func, args = args, kwargs = kwargs)
        t.start()
    return wrapper

@async
def cleanup_unread():
    """Destroy unread notes older than 30 days."""
    start_time = time.time()
    while True:
        for f in os.listdir('%s/data/' % here):
            file_mtime = os.stat('%s/data/%s', % (here, f))[8]
            if (start_time - file_mtime) >= 2592000 and 'hashcash.db' not in f:
                secure_remove('%s/data/%s', % (here, f))
        time.sleep(86400) # wait for 1 day

@async
def destroy_note(path):
    """Destroy read note when it is 3 minutes old.
    
    Keyword arguments:
    path -- an absolute path to the note to be destroyed
    """
    start_time = time.time()
    os.utime(path, (start_time, start_time))
    while True:
        if os.path.exists(path):
            file_mtime = os.stat(path)[8]
            if (start_time - file_mtime) >= 10800:
                secure_remove(path)
                break
        time.sleep(3600) # wait for 1 minute

def secure_remove(path):
    """Securely overwrite any file, then remove the file.

    Do not make any assumptions about the underlying filesystem, whether
    it's journaled, copy-on-write, or whatever.

    Keyword arguments:
    path -- an absolute path to the file to overwrite with random data
    """
    r = Random.new()
    with open(path, "r+") as f:
        for char in xrange(os.stat(f.name).st_size):
            f.seek(char)
            f.write(chr(r.read(1)))
    os.remove(path)

def verify_hashcash(token):
    """Return True or False based on the Hashcash token

    Valid Hashcash tokens must start with '0000' in the SHA hexdigest string.
    If not, then return False to redirect the user to an error page. If the
    token is valid, but has already been spent, then also return False to
    redirect the user to an error page. Otherwise, if the token is valid and
    has not been spent, append it to th hashcash.db file.

    Keyword arguments:
    token -- a proposed Hashcash token to valide
    """
    digest = SHA.new(token)
    with open('%s/data/hashcash.db' % here, 'a+') as f:
        if digest.hexdigest()[:4] == '0000' and digest not in f:
            f.write(token+'\n')
            return True
        else:
            return False

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
    pad = lambda s: s + (8 - len(s) % 8) * chr(8 - len(s) % 8)
    plain = pad(zlib.compress(plaintext.encode('utf-8')))
    if key_file:
        # create empty file with '.key' as an extension
        open('%s/data/%s.key' % (here, new_url), 'a').close()
    with open('%s/data/%s' % (here,new_url), 'w') as f:
        bf = Blowfish.new(key, Blowfish.MODE_ECB)
        ciphertext = bf.encrypt(plain)
        f.write(ciphertext.encode("base64"))

def note_decrypt(key, ciphertext):
    """Decrypt a ciphertext from a given URI file.

    Keyword arguments:
    key -- private key to decrypt the ciphertext
    ciphertext -- the message to be decrypted
    """
    unpad = lambda s : s[0:-ord(s[-1])]
    with open('%s/data/%s' % (here, ciphertext), 'r') as f:
        message = f.read()
    bf = Blowfish.new(key, Blowfish.MODE_ECB)
    plaintext = bf.decrypt(message.decode("base64"))
    return zlib.decompress(unpad(plaintext)).decode('utf-8')

def create_url():
    """Return a new random 128-bit URI for retrieval."""
    new_url = base64.urlsafe_b64encode(Random.new().read(16))[:22]
    if os.path.exists('%s/data/%s' % (here, new_url)):
        create_url()
    return new_url

@dnote.route('/', methods = ['POST','GET'])
def index():
    """Return the index.html for the main application."""
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
        token = request.form['hashcash']
        valid_token = verify_hashcash(token)
        if request.form['pass'] and valid_token:
            privkey = request.form['pass']
            key_file = True
            note_encrypt(privkey, plaintext, new_url, key_file)
            return render_template('post.html', random = new_url)
        elif not request.form['pass'] and valid_token:
            key_file = False
            note_encrypt(key, plaintext, new_url, key_file)
            return render_template('post.html', random = new_url)
        else:
            return render_template('invalid.html')
    else:
        return render_template('invalid.html')

@dnote.route('/<random_url>', methods = ['POST', 'GET'])
def fetch_url(random_url):
    """Return the decrypted note. Begin short destruction timer.
    
    Only 1 person should be able to view the note, even if the not has not yet
    been destroyed. As such, a lock file is created when the note is read, to
    prevent anyone else from also viewing it. A standard 404 error is thrown,
    as to not give any hints as to whether or not the note still exists.
    
    Keyword arguments:
    random_url -- Random URL representing the encrypted note
    """
    if os.path.exists('%s/data/%s.lock' % (here, random_url)):
        return render_template('404.html')
    elif os.path.exists('%s/data/%s.key' % (here,random_url)) and request.method != 'POST':
        return render_template('key.html', random = random_url)
    elif os.path.exists('%s/data/%s.key' % (here,random_url)) and request.method == 'POST':
        privkey = request.form['pass']
        try:
            open('%s/data/%s.lock' % (here, random_url), 'a').close()
            plaintext = note_decrypt(privkey, random_url)
            destroy_note('%s/data/%s' % (here, random_url))
            destroy_note('%s/data/%s.key' % (here, random_url))
            destroy_note('%s/data/%s.lock' % (here, random_url))
            return render_template('note.html', text = plaintext)
        except:
            return render_template('keyerror.html', random=random_url)
    else:
        open('%s/data/%s.lock' % (here, random_url), 'a').close()
        plaintext = note_decrypt(key, random_url)
        destroy_note('%s/data/%s' % (here, random_url))
        destroy_note('%s/data/%s.lock' % (here, random_url))
        return render_template('note.html', text = plaintext)

if __name__ == '__main__':
    dnote.debug = True
    cleanup_unread()
    dnote.run()
