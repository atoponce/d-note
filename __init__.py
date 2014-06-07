import base64
import os
import zlib
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA, SHA512
from Crypto.Protocol import KDF
from Crypto.Random import random
from flask import Flask, render_template, request, redirect, url_for

try:
    import dconfig
except ImportError:
    with open('dconfig.py','w') as f:
        f.write('uri_salt = "{0}"\n'.format(Random.new().read(16).encode('hex')))
        f.write('aes_salt = "{0}"\n'.format(Random.new().read(16).encode('hex')))
        f.write('mac_salt = "{0}"\n'.format(Random.new().read(16).encode('hex')))
    import dconfig

dnote = Flask(__name__)
here = dnote.root_path

if not os.path.exists('%s/data/' % here):
    os.makedirs('%s/data' % here)

def send_email(link, recipient):
    """Send the link via email to a recipient."""
    import email.utils
    import smtplib
    import time
    from email.mime.text import MIMEText
    msg = MIMEText("%s" % link)
    msg['To'] = email.utils.formataddr(('Self Destructing Notes', recipient))
    msg['From'] = email.utils.formataddr((fullname, fromaddr))
    s = smtplib.SMTP('localhost')
    s.sendmail(fromaddr, [recipient], msg.as_string())
    s.quit()

def async(func):
    """Return threaded wrapper decorator."""
    from threading import Thread
    def wrapper(*args, **kwargs):
        t = Thread(target = func, args = args, kwargs = kwargs)
        t.start()
    return wrapper

@async
def cleanup_unread():
    """Destroy unread notes older than 30 days."""
    while True:
        seek_time = time.time()
        for f in os.listdir('%s/data/' % here):
            file_mtime = os.stat('%s/data/%s' % (here, f))[8]
            if (seek_time - file_mtime) >= 2592000 and 'hashcash.db' not in f:
                secure_remove('%s/data/%s' % (here, f))
        time.sleep(86400) # wait for 1 day

def duress_key(random_url):
    """Return a duress key for Big Brother. The duress key is stored on disk in
    plaintext, and only returns lorem ipsum text."""
    import string
    chars = string.ascii_letters + string.digits
    dkey = ''.join(Random.random.choice(chars) for i in xrange(24))
    with open('%s/data/%s.dkey' % (here,random_url), 'w') as f:
        f.write(dkey)
    return dkey

def duress_text():
    """Return 5 random sentences of the Zen of Python."""
    import subprocess
    text = ''
    p = subprocess.Popen(('python','-c','import this'), stdout=subprocess.PIPE,)
    s = [x for x in p.communicate()[0].splitlines() if x != '']
    for i in range(5):
        text = text + Random.random.choice(s) + ' '
    return text

def secure_remove(path):
    """Securely overwrite any file, then remove the file.

    Do not make any assumptions about the underlying filesystem, whether
    it's journaled, copy-on-write, or whatever.

    Keyword arguments:
    path -- an absolute path to the file to overwrite with random data.
    """
    r = Random.new()
    with open(path, "r+") as f:
        for char in xrange(os.stat(f.name).st_size):
            f.seek(char)
            f.write(str(r.read(1)))
    os.remove(path)

def verify_hashcash(token):
    """Return True or False based on the Hashcash token

    Valid Hashcash tokens must start with '0000' in the SHA hexdigest string.
    If not, then return False to redirect the user to an error page. If the
    token is valid, but has already been spent, then also return False to
    redirect the user to an error page. Otherwise, if the token is valid and
    has not been spent, append it to the hashcash.db file.

    Keyword arguments:
    token -- a proposed Hashcash token to validate.
    """
    digest = SHA.new(token)
    with open('%s/data/hashcash.db' % here, 'a+') as f:
        if digest.hexdigest()[:4] == '0000' and token not in f.read():
            f.write(token+'\n')
            return True
        else:
            return False

def note_encrypt(key, mac_key, plaintext, fname, key_file):
    """Encrypt a plaintext to a URI file.

    All files are encrypted with AES in CBC mode. HMAC-SHA512 is used
    to provide authenticated encryption ( encrypt then mac ). No private keys
    are stored on the server.

    Keyword arguments:
    key -- aes private key to encrypt the plaintext.
    hmac_key -- hmac-sha1 key for authenticated encryption.
    plaintext -- the message to be encrypted.
    fname -- file to save the encrypted text to.
    """
    pad = lambda s: s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)
    plain = pad(zlib.compress(plaintext.encode('utf-8')))
    if key_file:
        # create empty file with '.key' as an extension
        open('%s/data/%s.key' % (here, fname), 'a').close()

    with open('%s/data/%s' % (here,fname), 'w') as f:
        iv = Random.new().read(AES.block_size) # Fixed block size to 16 bytes.
        aes = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = aes.encrypt(plain)
        ciphertext = iv + ciphertext
        # generate a hmac tag
        hmac = HMAC.new(mac_key,ciphertext,SHA512)
        ciphertext = hmac.digest() + ciphertext
        f.write(ciphertext)

def note_decrypt(key, mac_key, fname):
    """Decrypt the ciphertext from a given URI file.

    Keyword arguments:
    key -- aes private key to decrypt the plaintext
    hmac_key -- hmac-sha1 key for authenticated encryption
    fname -- filename containing the message to be decrypted
    """

    unpad = lambda s : s[0:-ord(s[-1])]
    with open('%s/data/%s' % (here, fname), 'r') as f:
        message = f.read()
    tag = message[:64]
    data = message[64:]
    iv = data[:16]
    body = data[16:]
    aes = AES.new(key, AES.MODE_CBC,iv)
    plaintext = aes.decrypt(body)
    # check the message tags, return 0 if is good
    # constant time comparison
    tag2 = HMAC.new(mac_key,data,SHA512).digest()
    hmac_check = 0
    for x, y in zip(tag, tag2):
        hmac_check |= ord(x) ^ ord(y)
    return hmac_check,zlib.decompress(unpad(plaintext)).decode('utf-8')

def create_url():
    """Generate enough randomness for filename, AES key, MAC key:

        - 128 bits for file name
        - 256 bits for AES-256 key
        - 512 bits for HMAC-SHA512 key

    Encode into a 22-byte URI.
    """
    uri = Random.new().read(16)
    uri_data = KDF.PBKDF2(uri,dconfig.uri_salt.decode("hex"),112)
    fname = base64.urlsafe_b64encode(uri_data[:16])[:22]
    key = uri_data[16:48] # 32 bytes for AES key
    mac_key = uri_data[48:] # 64 bytes for HMAC
    if os.path.exists('%s/data/%s' % (here, fname)):
        return create_url()
    # remove the last 2 "==" from the url
    new_url = base64.urlsafe_b64encode(uri)[:22]
    return {"new_url": new_url, "key": key, "mac_key": mac_key, "fname": fname}

def decode_url(url):
    """
    Takes a url, and returns the fname, key, hmac_key out of it

    keyword arguments:
    url -- the url after the FQDN provided by the client
    """
    # add the padding back
    url = url + "=="
    uri = base64.urlsafe_b64decode(url.encode("utf-8"))
    uri_data = KDF.PBKDF2(uri,dconfig.uri_salt.decode("hex"),112)
    fname = base64.urlsafe_b64encode(uri_data[:16])[:22]
    key = uri_data[16:48] # 32 bytes for AES key
    mac_key = uri_data[48:] # 64 bytes for HMAC
    return {"key": key, "mac_key": mac_key, "fname":fname}

@dnote.route('/', methods = ['GET'])
def index():
    """Return the index.html for the main application."""
    error = request.args.get('error',None)
    new_url = create_url()["new_url"]
    return render_template('index.html', random = new_url, error = error)

@dnote.route('/security/', methods = ['GET'])
def security():
    """Return the index.html for the security page."""
    return render_template('security.html')

@dnote.route('/faq/', methods = ['GET'])
def faq():
    """Return the index.html for the faq page."""
    return render_template('faq.html')

@dnote.route('/about/', methods = ['GET'])
def about():
    """Return the index.html for the about page."""
    return render_template('about.html')

@dnote.route('/post', methods = ['POST'])
def show_post():
    """Return the random URL after posting the plaintext."""
    new_url = request.form["new_url"]
    url_data = decode_url(new_url)
    key = url_data["key"]
    mac_key = url_data["mac_key"]
    fname = url_data["fname"]

    plaintext = request.form['paste']
    passphrase = request.form.get('pass',False)
    duress = request.form.get('duress',False)
    token = request.form['hashcash']

    if not verify_hashcash(token):
        return redirect(url_for('index',error='hashcash'))
    if duress and not passphrase:
        return redirect(url_for('index',error='duress'))

    if passphrase:
        key = KDF.PBKDF2(passphrase, dconfig.aes_salt.decode("hex"), 32)
        mac_key = KDF.PBKDF2(passphrase, dconfig.mac_salt.decode("hex"), 64)
        key_file = True
        note_encrypt(key, mac_key, plaintext, fname, key_file)
        if duress:
            dkey = duress_key(fname)
            return render_template('post.html', random = new_url, passphrase = passphrase, duress = dkey)
        return render_template('post.html', random = new_url, passphrase = passphrase)
    else:
        key_file = False
        note_encrypt(key, mac_key, plaintext, fname, key_file)
        return render_template('post.html', random = new_url)

@dnote.route('/<random_url>', methods = ['POST', 'GET'])
def fetch_url(random_url):
    """Return the decrypted note. Begin short destruction timer.

    Keyword arguments:
    random_url -- Random URL representing the encrypted note.
    """
    url_data = decode_url(random_url)
    key = url_data["key"]
    mac_key = url_data["mac_key"]
    fname = url_data["fname"]

    if not os.path.exists('%s/data/%s' % (here,fname)):
        return render_template('404.html'), 404
    elif os.path.exists('%s/data/%s.key' % (here,fname)) and request.method != 'POST':
        return render_template('key.html', random = random_url)
    elif os.path.exists('%s/data/%s.key' % (here,fname)) and request.method == 'POST':
        passphrase = request.form['pass']
        key = KDF.PBKDF2(passphrase, dconfig.aes_salt.decode("hex"), 32)
        mac_key = KDF.PBKDF2(passphrase, dconfig.mac_salt.decode("hex"), 64)
        if os.path.exists('%s/data/%s.dkey' % (here,fname)):
            with open('%s/data/%s.dkey' % (here,fname), 'r') as f:
                if passphrase in f:
                    secure_remove('%s/data/%s' % (here, fname))
                    secure_remove('%s/data/%s.key' % (here, fname))
                    secure_remove('%s/data/%s.dkey' % (here, fname))
                    return render_template('note.html', text = duress_text())
                else:
                    try:
                        hmac_check,plaintext = note_decrypt(key, mac_key, fname)
                        if hmac_check != 0 :
                            return render_template('keyerror.html', random = random_url)
                        else:
                            secure_remove('%s/data/%s' % (here, fname))
                            secure_remove('%s/data/%s.key' % (here, fname))
                            if os.path.exists('%s/data/%s.dkey' % (here, fname)):
                                secure_remove('%s/data/%s.dkey' % (here, fname))
                            return render_template('note.html', text = plaintext)
                    except:
                        return render_template('keyerror.html', random = random_url)
        else:
            try:
                hmac_check,plaintext = note_decrypt(key, mac_key, fname)
                if hmac_check != 0 :
                    return render_template('keyerror.html', random = random_url)
                else:
                    secure_remove('%s/data/%s' % (here, fname))
                    secure_remove('%s/data/%s.key' % (here, fname))
                    if os.path.exists('%s/data/%s.dkey' % (here, fname)):
                        secure_remove('%s/data/%s.dkey' % (here, fname))
                    return render_template('note.html', text = plaintext)
            except:
                return render_template('keyerror.html', random = random_url)
    else:
        hmac_check,plaintext = note_decrypt(key, mac_key, fname)
        if hmac_check != 0 :
            return render_template('404.html'), 404
        else:
            secure_remove('%s/data/%s' % (here, fname))
            return render_template('note.html', text = plaintext)

if __name__ == '__main__':
    dnote.debug = True
    #cleanup_unread()
    dnote.run()
