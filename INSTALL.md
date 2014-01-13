Installation
============

d-note is a Python Flask web application that requires a couple of libraries to
be installed. I'll assume you're using Debian to install software. First,
install both `python-flask` and `python-crypto`:

    # apt-get install python-flask python-crypto

Now make a directory under your web root to clone the Git repository:

    # mkdir /var/www/dnote/
    # git clone https://github.com/atoponce/d-note.git /var/www/dnote/dnote

Install `libapache2-mod-wsgi` to server the Python Flask web framework under
Apache:

    # apt-get install libapache2-mod-wsgi

Create a `dnote.wsgi` file under the web root:

    # touch /var/www/dnote/dnote.wsgi

Add the following contents to that file:

    #!/usr/bin/python
    import sys
    import logging
    logging.basicConfig(stream=sys.stderr)
    sys.path.insert(0,"/var/www/dnote/")
    from dnote import dnote as application
 
Now configure Apache to server the application. Create
`/etc/apache2/site-available/` with the following contents. It's important that
you serve the application over SSL. See additional Apache documentation as
necessary.

    <Virtualhost *:443>
        DocumentRoot /var/www/dnote/
        CustomLog /var/log/apache2/access.log combined
        ServerName www.example.com
        ServerAlias www.example.com example.com
        ServerAdmin webmaster@example.com
        <Directory /var/www/dnote>
            Options -Indexes FollowSymLinks
        </Directory>
        WSGIScriptAlias / /var/www/dnote/dnote.wsgi
        <Directory /var/www/dnote/dnote/>
            Order allow,deny
            Allow from all
        </Directory>
            Alias /d/static /var/www/dnote/dnote/static
        <Directory /var/www/dnote/dnote/static/>
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
