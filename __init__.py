import base64
import email.utils
import os
import smtplib
import string
import time
import zlib
import Crypto
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import HMAC
from Crypto.Hash import SHA
from Crypto.Random import random
from pbkdf2 import PBKDF2
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for
from threading import Thread

# BEGIN CHANGEME.
fromaddr = "no-reply@example.com"
fullname = "John Doe"
salt1 = "52f9a7242412eed8d607f80a4a97d41b" # Output from Random.new().read(16).encode("hex")
salt2 = "a79f3ab9732cb999afec457267e49fea"

# END CHANGEME.


# SOME CONSTANTS
FILE_NAME_LENGTH = 16 # number of bytes of randomness for file names
BLOCK_SIZE = 16 # for AES128 
MAC_SIZE = 20 # for HMAC-SHA1
DURESS_TEXT = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."


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
    chars = string.ascii_letters + string.digits
    dkey = ''.join(random.choice(chars) for i in xrange(24))
    with open('%s/data/%s.dkey' % (here,random_url), 'w') as f:
        f.write(dkey)
    return dkey

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
            f.write(str(r.read(1)))
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

def note_encrypt(key, mac_key, plaintext, fname, key_file):
    """Encrypt a plaintext to a URI file.

    All files are encrypted with AES in CBC mode. HMAC-SHA1 is used
    to provide authenticated encryption ( encrypt then mac ). No private keys are stored 
    on the server

    Keyword arguments:
    key -- aes private key to encrypt the plaintext
    hmac_key -- hmac-sha1 key for authenticated encryption
    plaintext -- the message to be encrypted
    fname -- file to save the encrypted text to
    """
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
    plain = pad(plaintext.encode('utf-8'))
    if key_file:
        # create empty file with '.key' as an extension
        open('%s/data/%s.key' % (here, fname), 'a').close()
    with open('%s/data/%s' % (here,fname), 'w') as f:
        iv = Random.new().read(BLOCK_SIZE)
        aes = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = aes.encrypt(plain)
        ciphertext = iv + ciphertext
        # generate a hmac tag
        hmac=HMAC.new(mac_key,ciphertext,Crypto.Hash.SHA)
        ciphertext = hmac.digest() + ciphertext
        f.write(ciphertext.encode("base64"))

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
    message = message.decode("base64")
    tag = message[:MAC_SIZE]
    data = message[MAC_SIZE:]
    iv = data[:BLOCK_SIZE]
    body = data[BLOCK_SIZE:]
    aes = AES.new(key, AES.MODE_CBC,iv)
    plaintext = aes.decrypt(body)
    # check the message tags, return 0 if is good 
    # constant time comparison
    tag2 = HMAC.new(mac_key,data,Crypto.Hash.SHA).digest()
    hmac_check = 0
    for x, y in zip(tag, tag2):
        hmac_check |= ord(x) ^ ord(y)
    return hmac_check,unpad(plaintext).decode('utf-8')

def create_url():
    """Generate enough randomness for filename, aes key, mac key.
     
    128 bits for file name
    128 bits for AES-128 key
    160 bits for HMAC-SHA1 key      
  
    and encode it into 70byte URI
    """
    uri_rand=Random.new().read(52) 
    fname = base64.urlsafe_b64encode(uri_rand[:16])[:22]
    key = uri_rand[16:32] # 16 bytes for AES key
    mac_key = uri_rand[32:] # 20 bytes for HMAC
    if os.path.exists('%s/data/%s' % (here, fname)):
        create_url()
    # remove the last 2 "==" from the url
    new_url = base64.urlsafe_b64encode(uri_rand)[:70]
    return {"new_url": new_url, "key": key, "mac_key": mac_key, "fname": fname}

def decode_url(url):
    """ 
    Takes a url, and returns the fname, key, hmac_key out of it
    """
    # add the padding back
    url = url + "=="
    uri_rand = base64.urlsafe_b64decode(url.encode("utf-8"))
    fname = base64.urlsafe_b64encode(uri_rand[:16])[:22]
    key = uri_rand[16:32] # 16 bytes for AES key
    mac_key = uri_rand[32:] # 20 bytes for HMAC
    return {"key": key, "mac_key": mac_key, "fname":fname}

 

@dnote.route('/', methods = ['GET'])
def index():
    """Return the index.html for the main application."""
    error = None
    new_url = create_url()["new_url"]
    return render_template('index.html', random = new_url, error=error)

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

@dnote.route('/post/<new_url>', methods = ['POST', 'GET'])
def show_post(new_url):
    """Return the random URL after posting the plaintext.
    
    Keyword arguments:
    new_url -- encrypted file representing the unique URL
    if a user provided string is used for key generation
    use PBKDF2 to generate secure keys from it.
    """
    url_data=decode_url(new_url)
    key = url_data["key"]
    mac_key = url_data["mac_key"]
    fname = url_data["fname"]
    if request.method == 'POST':
        plaintext = request.form['paste']
        token = request.form['hashcash']
        valid_token = verify_hashcash(token)
        if request.form.get('duress', False) and request.form['pass'] and valid_token:
            dkey = duress_key(fname)
            passphrase = request.form['pass']
            key = PBKDF2(passphrase, salt1.decode("hex")).read(16)
            mac_key = PBKDF2(passphrase, salt2.decode("hex")).read(20)
            key_file = True
            note_encrypt(key, mac_key, plaintext, fname, key_file)
            return render_template('post.html', random=new_url, passphrase=passphrase, duress=dkey)
        elif request.form['pass'] and valid_token:
            passphrase = request.form['pass']
            key = PBKDF2(passphrase, salt1.decode("hex")).read(16)
            mac_key = PBKDF2(passphrase, salt2.decode("hex")).read(20)
            key_file = True
            note_encrypt(key, mac_key, plaintext, fname, key_file)
            return render_template('post.html', random=new_url, passphrase=passphrase)
        elif not request.form['pass'] and valid_token:
            key_file = False
            note_encrypt(key, mac_key, plaintext, fname, key_file)
            return render_template('post.html', random=new_url)

@dnote.route('/<random_url>', methods = ['POST', 'GET'])
def fetch_url(random_url):
    """Return the decrypted note. Begin short destruction timer.
    
    Keyword arguments:
    random_url -- Random URL representing the encrypted note
    """
    url_data=decode_url(random_url)
    key = url_data["key"]
    mac_key = url_data["mac_key"]
    fname = url_data["fname"]

    if not os.path.exists('%s/data/%s' % (here,fname)):
        return render_template('404.html'), 404
    elif os.path.exists('%s/data/%s.key' % (here,fname)) and request.method != 'POST':
        return render_template('key.html', random = random_url)
    elif os.path.exists('%s/data/%s.key' % (here,fname)) and request.method == 'POST':
        passphrase = request.form['pass']
        key = PBKDF2(passphrase, salt1.decode("hex")).read(16)
        mac_key = PBKDF2(passphrase, salt2.decode("hex")).read(20)
        if os.path.exists('%s/data/%s.dkey' % (here,fname)):
            with open('%s/data/%s.dkey' % (here,fname), 'r') as f:
                if passphrase in f:
                    secure_remove('%s/data/%s' % (here, fname))
                    secure_remove('%s/data/%s.key' % (here, fname))
                    secure_remove('%s/data/%s.dkey' % (here, fname))
                    # return render_template('404.html'), 404
                    return render_template('note.html', text = DURESS_TEXT)
                else:
                    try:
                        hmac_check,plaintext = note_decrypt(key, mac_key, fname)
                        if hmac_check != 0 :
                            return render_template('keyerror.html', random=random_url)
                        else: 
                            secure_remove('%s/data/%s' % (here, fname))
                            secure_remove('%s/data/%s.key' % (here, fname))
                            if os.path.exists('%s/data/%s.dkey' % (here, fname)):
                                secure_remove('%s/data/%s.dkey' % (here, fname))
                            return render_template('note.html', text = plaintext)
                    except:
                        return render_template('keyerror.html', random=random_url)
        else:
            try:
                hmac_check,plaintext = note_decrypt(key, mac_key, fname)
                if hmac_check != 0 :
                    return render_template('keyerror.html', random=random_url)
                else: 
                    secure_remove('%s/data/%s' % (here, fname))
                    secure_remove('%s/data/%s.key' % (here, fname))
                    if os.path.exists('%s/data/%s.dkey' % (here, fname)):
                        secure_remove('%s/data/%s.dkey' % (here, fname))
                    return render_template('note.html', text = plaintext)
            except:
                return render_template('keyerror.html', random=random_url)
    else:
        hmac_check,plaintext = note_decrypt(key, mac_key, fname)
        if hmac_check != 0 :
            return render_template('404.html'), 404
        else:
            secure_remove('%s/data/%s' % (here, fname))
            return render_template('note.html', text = plaintext)

if __name__ == '__main__':
    dnote.debug = True
    cleanup_unread()
    dnote.run()
