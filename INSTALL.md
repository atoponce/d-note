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
