servembtiles.py
================

'servembtiles.py' is a pure python3 wsgi application for serving [MBTiles](https://github.com/mapbox/mbtiles-spec).
MBTiles can be exported from [Tilemill](https://www.mapbox.com/tilemill/).  (If you do web-maps you should checkout tilemill)

The application's MBTiles filepath can be defined in the 'settings.py' variable, "MBTILES_ABSPATH".
The application's tile image file extension can also be set via the 'settings.py' variable, "MBTILES_TILE_EXT".

Requests are expected to follow the TMS addressing scheme. (For example, '/z/x/y.png')
See (http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/) for details.

In addition, the `/metadata/` URL is available to view the .mbtiles file's metadata table in `json` format.
(And if the included sample configurations and `index.html` are used, `/index.html` provides a test map to confirm that your tiles are being served from the defined `.mbtiles` file)

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

## Setting up servembtiles with uWSGI & nginx

Configured for Ubuntu 14.04:
    
1. Create venv for servembtiles
    ```
    sudo mkdir -m 777 /var/www/servembtiles
    python3 -m venv /var/www/servembtiles
    mkdir /var/www/servembtiles/repo
    # activate venv
    cd /var/www/servembtiles
    source bin/activate
    ```
    
2. Clone servembtiles project
    ```
    git clone https://github.com/monkut/servembtiles.git repo
    chmod 777 /var/www/servembtiles/repo
    ```

3.  Install uwsgi (application server)
    ```
    cd /var/www/servembtiles/repo
    pip install -r requirements.txt
    ```
    

##Sample Nginx Proxy Configuration

Prepared using:
nginx version: nginx/1.4.6 (Ubuntu)
On ubuntu 14.04

Referenced:
https://www.digitalocean.com/community/tutorials/understanding-nginx-http-proxying-load-balancing-buffering-and-caching

See `conf/servembtiles.nginx.conf` for sample.

NOTE: Even if this sample is used, `/etc/nginx/nginx.conf` needs to be updated, see below.

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
# sample servembtiles for proxy server caching
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
