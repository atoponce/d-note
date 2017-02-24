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

Notes:
 - Change <www.yourwebsite.tld> to your own URL.
 - Logs changed to only contain method, not the actualy request to avoid logging Note URLs in local logs
 - Secure headers
 - Replace <www.yourotherwebsite.tld> with your own second public URL
 - Set your own public public cert, private key and intermediate CA file paths
 - Fix 404 is to make sure a template error message will get used in those conditions
 - "## Deny access" can be used to limit those who can store a Note

<Virtualhost *:80>
    Redirect permanent / https://<www.yourwebsite.tld>/
</VirtualHost>

<Virtualhost *:443>
    DocumentRoot /var/www/
    ServerName <www.yourwebsite.tld>
    ServerAdmin webmaster@<www.yourwebsite.tld>

    LogFormat "%h %l %u %t \"%m\" %>s %O \"%{User-Agent}i\"" securelog
    CustomLog /var/log/apache2/access.log securelog

    Header always edit Set-Cookie ^(.*)$ $1;secure
    Header always set X-Frame-Options "DENY"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Strict-Transport-Security "max-age=315360000; includeSubDomains; preload"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Permitted-Cross-Domain-Policies "none"

    <Directory /var/www/>
        Options -Indexes +FollowSymLinks
    </Directory>

    WSGIScriptAlias / /var/www/dnote.wsgi

    <Directory /var/www/dnote/>
        Order allow,deny
        Allow from all
    </Directory>

        Alias /d/static /var/www/dnote/static

    <Directory /var/www/dnote/static/>
        Order allow,deny
        Allow from all
    </Directory>

    # In case you want to limit access
    <Location />
        #order deny,allow
        #deny from all
        #allow from 127.0.0.1
    </Location>

    ## In case you want to limit specific access
    #<Location ~ "/.+">
    #    order deny,allow
    #    allow from all
    #</Location>

    # Enable rewriteEngine
    RewriteEngine On

    # Redirect IP based requests to hostname
    RewriteCond %{HTTP_HOST} !^<www.yourwebsite.tld>$
    RewriteRule /.* https://<www.yourwebsite.tld>/ [R]

    ## Deny access to parts where data is entered
    ## Redirect Internet users from / to public website
    #RewriteCond "%{REMOTE_ADDR}" "!=127.0.0.1"
    #RewriteCond "%{REQUEST_URI}" "^/$"          [OR]
    #RewriteCond "%{REQUEST_URI}" "^/post$"      [OR]
    #RewriteCond "%{REQUEST_URI}" "^/about/$"    [OR]
    #RewriteCond "%{REQUEST_URI}" "^/security/$" [OR]
    #RewriteCond "%{REQUEST_URI}" "^/faq/$"
    #RewriteRule "^/(.*)$" "https://<www.yourotherwebsite.tld>/" [R,L]

    # Fix 404
    RewriteCond "%{REQUEST_URI}" "!^/post$"
    RewriteCond "%{REQUEST_URI}" "!^/about/$"
    RewriteCond "%{REQUEST_URI}" "!^/security/$"
    RewriteCond "%{REQUEST_URI}" "!^/faq/$"
    RewriteCond "%{REQUEST_URI}" "^/.*/$"
    RewriteRule "^/(.*)$" "https://<www.yourwebsite.tld>/error" [R,L]

    # Enable and configure SSL
    SSLEngine               on
    SSLProtocol             all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite          EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH
    SSLHonorCipherOrder     on
    SSLCertificateFile      /etc/apache2/ssl/your_public_cert.crt
    SSLCertificateKeyFile   /etc/apache2/ssl/your_private_key.key
    SSLCertificateChainFile /etc/apache2/ssl/ca_intermediate_certificates.pem
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
