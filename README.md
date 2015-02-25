servembtiles.py
================

'servembtiles.py' is a pure python3 wsgi application for serving [MBTiles](https://github.com/mapbox/mbtiles-spec).
MBTiles can be exported from [Tilemill](https://www.mapbox.com/tilemill/).  (If you do web-maps you should checkout tilemill)

The application's MBTiles filepath can be defined in the 'settings.py' variable, "MBTILES_ABSPATH".
The application's tile image file extension can also be set via the 'settings.py' variable, "MBTILES_TILE_EXT".

Requests are expected to follow the TMS addressing scheme. (For example, '/z/x/y.png')
See (http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/) for details.

In addition, the `/metadata/` URL is available to view the .mbtiles file's metadata table in `json` format.

This includes a simple test server for verification purposes.
Ideally, this should probably be served via [Nginx](http://nginx.com/resources/glossary/reverse-proxy-server/) or apache2, with reverse proxy caching.

##Test Server Usage

The test server is implemented through `from wsgiref.simple_server import make_server`.

```
$ python3 servembtiles.py --serve --filepath exports/OSMBright.mbtiles
2015-02-24 16:27:45,473 - servembtiles - INFO - FILEPATH: /home/myuser/mapdata/exports/OSMBright.mbtiles
2015-02-24 16:27:45,473 - servembtiles - INFO - TILE EXT: .png
2015-02-24 16:27:45,474 - servembtiles - INFO - ADDRESS : localhost
2015-02-24 16:27:45,474 - servembtiles - INFO - PORT    : 8005
```

##Dependencies

None!

##Why?

I was looking for a simple mbtiles python server implementation and I've been trying to move more and more of my work to python3.

I found [django-mbtiles](https://pypi.python.org/pypi/django-mbtiles/1.3) which seems to do the same, but not with python3 and it requires django.
It appears to have more features though, so if this doesn't meet your needs you may want to take a look at it.

##Sample servembtiles.conf apache2 configuration file

Configured for Ubuntu 14.04:
    Server version: Apache/2.4.7 (Ubuntu)

Edit the `/etc/apache2/ports.conf` adding the VirtualHost port number to the `ports.conf` file (for example, 'Listen 8005').
This file goes in the `sites-available` apache2 directory:

```
<VirtualHost *:8005>
        # copy to /etc/apache2/sites-available/servembtiles.conf
        # Referenced:
        # https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/modwsgi/

        # The ServerName directive sets the request scheme, hostname and port that
        # the server uses to identify itself. This is used when creating
        # redirection URLs. In the context of virtual hosts, the ServerName
        # specifies what hostname must appear in the request's Host: header to
        # match this virtual host. For the default virtual host (this file) this
        # value is not decisive as it is used as a last resort host regardless.
        # However, you must set it for any further virtual host explicitly.
        ServerName servembtiles
        ServerAlias servembtiles
        ServerAdmin admin@server.com

        # static and media directories should be outside of "repository".
        Alias /robots.txt /var/www/serve-mbtiles/robots.txt
        Alias /favicon.ico /var/www/serve-mbtiles/favicon.ico

        # Referenced:
        # https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide#Delegation_To_Daemon_Process
        WSGIDaemonProcess servembtiles processes=2 threads=15 display-name=%{GROUP} python-path=/var/www/serve-mbtiles:/usr/local/lib/python3.4/dist-packages
        WSGIProcessGroup servembtiles
        WSGIScriptAlias / /var/www/serve-mbtiles/servembtiles.py

        <Directory /var/www/serve-mbtiles>
            <Files servembtiles.py>
                Require all granted
            </Files>
        </Directory>

        ErrorLog ${APACHE_LOG_DIR}/mbtiles_error.log
        CustomLog ${APACHE_LOG_DIR}/mbtiles_access.log combined
</VirtualHost>

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet
```

Once added run `sudo a2siteen servembtiles.conf` and restart apache via `sudo service apache2 restart`.



##Sample Nginx Proxy Configuration

Prepared using:
nginx version: nginx/1.4.6 (Ubuntu)
On ubuntu 14.04

Referenced:
https://www.digitalocean.com/community/tutorials/understanding-nginx-http-proxying-load-balancing-buffering-and-caching

###Nginx Installation

```
$ sudo apt-get update
$ sudo apt-get install nginx
```

After install nginx configuration available at, `/etc/nginx`.

###Update http config in `/etc/nginx/nginx.conf` adding the following above the "Virtual Host Configs":

        ##
        # Caching-Proxy Configs
        ##
        proxy_cache_path /var/lib/nginx/cache levels=1:2 keys_zone=mbtilescache:8m max_size=50m;
        proxy_cache_key "$request_uri";
        proxy_cache_valid 200 302 30m;
        proxy_cache_valid 404 1m;

###Create `/etc/nginx/sites-available/servembtiles.conf`

```
# sample servembtiles for proxy server
server {
    # Change if using another port
    # --> NOTE:  Apache may already be listening on 80
    listen 80 default_server;
    listen [::]:80 default_server ipv6only=on;

    # Make site accessible from http://localhost/
    server_name <IP of Machine>; # IP of machine we're serving from

    location / {
        proxy_cache mbtilescache;
        #proxy_cache_bypass $http_cache_control;  # not clear how this affects the mbtiles serving use-case...
        add_header X-Proxy-Cache $upstream_cache_status;

        # servembtils.py port (configured in apache2)
        proxy_pass http://localhost:8005;
    }
}
```

The 'X-Proxy-Cache' header is added and can be used to confirm if the nginx cache is HIT, MISS or BYPASS.

Refer to the following for details:
https://serversforhackers.com/nginx-caching/



###Create the cache directory

Create the cache directory defined in `/etc/nginx/nginx.conf`.

```
$ sudo mkdir -p /var/lib/nginx/cache
$ sudo chown www-data /var/lib/nginx/cache
$ sudo chmod 700 /var/lib/nginx/cache
```
