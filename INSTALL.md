Installation
============

d-note is a Python Flask web application that requires a couple of libraries to
be installed. I&#39;ll assume you&#39;re using Debian to install software. First,
install `python-flask` and `python-crypto`:

    # apt-get install python-flask python-crypto

The correct `python-crypto` package should be coming from
https://www.dlitz.net/software/pycrypto/

Configuration
-------------
Run the following from a terminal to setup the configuration file and data
storage directory before launching the application:

    $ python setup.py install

After the application is installed, the dconfig.py needs to be generated.

Edit the dnote.ini in this directory and update the 'config_path' value in
the [default] section. It is recommended that this value be either either
/etc/dnote or ~/.dnote.  Once edited, copy the dnote.ini file to the directory
you created.

Once copied, run the following:

    $ generate_dnote_hashes

This will create a `dconfig.py` in the proper directory. This file should
have salts with random hexadecimal strings as their values.

Apache Setup
------------
Install `libapache2-mod-wsgi` to server the Python Flask web framework under
Apache:

    # apt-get install libapache2-mod-wsgi

Create a `dnote.wsgi` file under the web root:

    # touch /var/www/dnote.wsgi

Add the following contents to that file:

    #!/usr/bin/python
    import sys
    import logging
    logging.basicConfig(stream=sys.stderr)
    from dnote import DNOTE as application

Now configure Apache to server the application. Create
`/etc/apache2/site-available/` with the following contents. It&#39;s important
that you serve the application over SSL. See additional Apache documentation as
necessary.

    <Virtualhost *:443>
        DocumentRoot /var/www/
        CustomLog /var/log/apache2/access.log combined
        ServerName www.example.com
        ServerAlias www.example.com example.com
        ServerAdmin webmaster@example.com
        <Directory /var/www/>
            Options -Indexes FollowSymLinks
        </Directory>
        WSGIScriptAlias / /var/www/dnote.wsgi
        <Directory /var/www/dnote/
            Order allow,deny
            Allow from all
        </Directory>
            Alias /d/static /var/www/dnote/static
        <Directory /var/www/dnote/static/>
            Order allow,deny
            Allow from all
        </Directory>

        SSLEngine on
        SSLCertificateFile /etc/ssl/certs/www_example_com.crt
        SSLCertificateKeyFile /etc/ssl/private/www_example_com.key
        SSLHonorCipherOrder On
    </VirtualHost>

Restart Apache, and verify that the site loads:

    # service apache2 restart

Nginx Setup
-----------
Install uwsgi:

    # apt-get install uwsgi uwsgi-core uwsgi-extra uwsgi-plugin-python

Create a uwsgi.ini file in the directory with the application:

    # touch /var/www/dnote/uwsgi.ini

And add the following to that file (you can tweak these settings as required):

    [uwsgi]
    socket = 127.0.0.1:8081
    chdir = /python/path/site-packages/dnote-1.0.1-py2.7.egg/dnote
    plugin = python
    module = __init__:dnote
    processes = 4
    threads = 2
    stats = 127.0.0.1:9192
    uid = www-data
    gid = www-data
    logto = /var/log/dnote.log

You can now start the dnote application by running:

    # /usr/bin/uwsgi -c /var/www/dnote/uwsgi.ini

This will start uwsgi in the foreground.  To start it as a
daemon:

    # /usr/bin/uwsgi -d -c /var/www/dnote/uwsgi.ini

You may want to add this to an init or upstart script, see:
http://uwsgi-docs.readthedocs.org/en/latest/Management.html

Now lets configure nginx. A common example would be if you wanted it 
to be avaliable under http://yoursite.tld/dnote. To acheive this, add
the following to your sites config (again, you can tweak thsi as needed):

    location = /dnote { rewrite ^ /dnote/; }
    location /dnote/ { try_files $uri @dnote; }
    location @dnote {
        include uwsgi_params;
        uwsgi_param SCRIPT_NAME /dnote;
        uwsgi_modifier1 30;
        uwsgi_pass 127.0.0.1:8081;
    }

And tada, restart the Nginx server and you should have a working dnote setup.


Troubleshooting
---------------
If you are getting any internal service errors make sure to verify that the
files in /var/www/dnote/dnote are readable by the webserver, and that
/var/www/dnote/dnote/data/hashcash.db is writable as well.

If you have trouble getting the app to load using uwsgi, try setting up a
dnote.wsgi file (as in the Apache directions above) and using uwsgi-file
in the uwsgi.ini file instead of module, like this:

    [uwsgi]
    socket = 127.0.0.1:8081
    chdir = /python/path/site-packages/dnote-1.0.1-py2.7.egg/dnote
    plugin = python
    wsgi-file = /var/www/dnote.wsgi
    processes = 4
    threads = 2
    stats = 127.0.0.1:9192
    uid = www-data
    gid = www-data
    logto = /var/log/dnote.log



These are some notes I made for CentOS 7.9, it still needs cleaning, I just needed a place to dump it for now
---------------------------------------------------------------------------------------------------------------

```sh

I still need to update the install notes properly explain exactly how it’s installed but here it is in a nutshell:

Pre-requisites:

Python 3.6.8 (this is the version I used because that’s what comes with CentOS)

The following CentOS packages that are needed for Python3 and http mod_wsgi:

mod_wsgi.x86_64

python3-mod_wsgi.x86_64

python3-libs.x86_64

python3-pip.noarch

python3-setuptools.noarch

Install it all in one command:

yum install python3-mod_wsgi.x86_64 python3-libs.x86_64 python3-pip.noarch python3-setuptools.noarch

Once the above is installed.

Apache is used as the web server, and it uses qsgi to launch the python code.

This is the Apache httpd config file location:

/etc/httpd/conf.d/share-le-ssl.conf

And this is the contents, what’s important is the line that saysWSGIScriptAlias and the few lines below that, the other stuff is unrelated, just putting it here for full context.

# customise the links as per you own deployment

<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName dnote.domain.com
    ServerAdmin dnote@domain.com
    ServerAlias www.dnote.domain.com
    DocumentRoot /var/www/html
    ErrorLog /var/log/httpd/share-error.log
    CustomLog /var/log/httpd/share-requests.log combined

    WSGIScriptAlias /dnote /var/www/dnote/wsgi.py
    <Directory /var/www/dnote/>
        Options -Indexes
        Options FollowSymLinks
        Order allow,deny
        Allow from all
    </Directory>
    Alias /d/static /var/www/dnote/static
    <Directory /var/www/dnote/static/>
        Order allow,deny
        Allow from all
    </Directory>

SSLCertificateFile /etc/letsencrypt/live/dnote.domain.com/cert.pem
SSLCertificateKeyFile /etc/letsencrypt/live/dnote.domain.com/privkey.pem
Include /etc/letsencrypt/options-ssl-apache.conf
SSLCertificateChainFile /etc/letsencrypt/live/dnote.domain.com/chain.pem
</VirtualHost>
</IfModule>
 

Steps to install it are:

clone the git repo from:

git clone git@github.com:Pyroseza/d-note.git

checkout the py3 branch

cd d-note

git checkout py3

zip it up

cd ..

zip -r d-note.zip d-note

upload it to /tmp on your server hosting this: dnote.domain.com

scp d-note.zip dnote.domain.com:/tmp

run these commands:

cd /tmp

rm -rf d-note

unzip d-note.zip

cd d-note/

python3 setup.py install

systemctl restart httpd

tail -f /etc/httpd/logs/share-requests.log /etc/httpd/logs/share-error.log

The bulk of the code gets installed under Python3’s site-packages, here:

/usr/local/lib/python3.6/site-packages/dnote-2.0.0-py3.6.egg/

The wsgi server file gets installed here:

/var/www/dnote/wsgi.py

and the config gets installed here:

/etc/dnote/d-note.ini
```
