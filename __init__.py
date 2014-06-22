"""This module sets up the paths for the Flask web application."""
import os
import utils
from Crypto import Random
from flask import Flask, render_template, request, redirect, url_for
from note import Note

DNOTE = Flask(__name__)
HERE = DNOTE.root_path

def async(func):
    """Return threaded wrapper decorator.

    Keyword arguments:
    func -- the function this decorator is threading"""

    from threading import Thread
    def wrapper(*args, **kwargs):
        """Decorator for asynchronous note destruction."""
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
    return wrapper

@async
def cleanup_unread():
    """Destroy unread notes older than 30 days."""

    import time
    while True:
        seek_time = time.time()
        for note in os.listdir('%s/data/' % HERE):
            file_mtime = os.stat('%s/data/%s' % (HERE, note))[8]
            if ((seek_time - file_mtime) >= 2592000
                    and 'hashcash.db' not in note):
                Note.secure_remove('%s/data/%s' % (HERE, note))
        time.sleep(86400) # wait for 1 day

@DNOTE.route('/', methods=['GET'])
def index():
    """Return the index.html for the main application."""
    error = request.args.get('error', None)
    note = Note()
    return render_template('index.html', random=note.url, error=error)

@DNOTE.route('/security/', methods=['GET'])
def security():
    """Return the index.html for the security page."""
    return render_template('security.html')

@DNOTE.route('/faq/', methods=['GET'])
def faq():
    """Return the index.html for the faq page."""
    return render_template('faq.html')

@DNOTE.route('/about/', methods=['GET'])
def about():
    """Return the index.html for the about page."""
    return render_template('about.html')

@DNOTE.route('/post', methods=['POST'])
def show_post():
    """Return the random URL after posting the plaintext."""
    new_url = request.form["new_url"]
    note = Note(new_url)
    note.plaintext = request.form['paste']

    passphrase = request.form.get('pass', False)
    token = request.form['hashcash']

    if not utils.verify_hashcash(token):
        return redirect(url_for('index', error='hashcash'))

    if passphrase:
        note.set_passphrase(passphrase)
        note.encrypt()
        note.duress_key()
        return render_template('post.html', random=note.url,
                               passphrase=note.passphrase, duress=note.dkey)
    else:
        note.encrypt()
        return render_template('post.html', random=note.url)

@DNOTE.route('/<random_url>', methods=['POST', 'GET'])
def fetch_url(random_url):
    """Return the decrypted note. Begin short destruction timer.

    Keyword arguments:
    random_url -- Random URL representing the encrypted note."""

    note = Note(random_url)

    if not note.exists():
        return render_template('404.html'), 404
    elif not note.decrypt() and request.method !='POST':
        return render_template('key.html', random = note.url)
    elif request.method == 'POST':
        passphrase = request.form['pass']
        note.set_passphrase(passphrase)
        if passphrase == note.dkey:
            note.secure_remove()
            return render_template('note.html', text = utils.duress_text())
    if note.decrypt():
        note.secure_remove()
        return render_template('note.html', text = note.plaintext)
    else:
        return render_template('keyerror.html', random = note.url)

if __name__ == '__main__':
    DNOTE.debug = True
    #cleanup_unread()
    DNOTE.run()
