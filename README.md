# servembtiles (MBTiles Tile Map Server)

'servembtiles.py' is a pure python3 wsgi application for serving [MBTiles](https://github.com/mapbox/mbtiles-spec).
MBTiles can be exported from [Tilemill](https://www.mapbox.com/tilemill/).  (If you do web-maps you should checkout tilemill)

The application's MBTiles filepath can be defined in the 'settings.py' variable, "MBTILES_ABSPATH".
The application's tile image file extension can also be set via the 'settings.py' variable, "MBTILES_TILE_EXT".

By default requests are expected to follow the TMS addressing scheme. (For example, '/z/x/y.png')
See (http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/) for details.
The Google maps XYZ scheme is supported by setting the *USE_OSGEO_TMS_TILE_ADDRESSING* value to *False* in the 'settings.py' file.

In addition, the `/metadata/` URL is available to view the .mbtiles file's metadata table in `json` format.
(And if the included sample configurations and `index.html` are used, `/index.html` provides a test map to confirm that your tiles are being served from the defined `.mbtiles` file)

This includes a simple test server for verification purposes.
The Installation section below describes how to configure this to serve tiles with reverse-proxy caching using Nginx,
with the configuration files included in this project.

##Test Server Usage

The test server is implemented through `from wsgiref.simple_server import make_server`.

```
$ python3 servembtiles.py --serve --filepath exports/OSMBright.mbtiles
2015-02-24 16:27:45,473 - servembtiles - INFO - FILEPATH: /home/myuser/mapdata/exports/OSMBright.mbtiles
2015-02-24 16:27:45,473 - servembtiles - INFO - TILE EXT: .png
2015-02-24 16:27:45,474 - servembtiles - INFO - ADDRESS : localhost
2015-02-24 16:27:45,474 - servembtiles - INFO - PORT    : 8005
```


## Requirements

- Python 3.5.X

## settings.py

The 'settings.py' file contains the following values:

    * MBTILES_ABSPATH - The absolute path to the mbtiles file to serve

    * MBTILES_TILE_EXT - The image extension to use (".png", ".jpg", ".jpeg")

    * USE_OSGEO_TMS_TILE_ADDRESSING - True (default) set to False to use Google XYZ addressing.

## Installation

This section describes the initial application installation method on ubuntu 14.04.

1. Create 'venv' on target server:

    ```console
    $ cd /var/www
    $ sudo mkdir servembtiles
    $ sudo chmod 777 servembtiles
    $ python3 -m venv servembtiles
    ```

2. Clone 'servembtiles' repository:

    ```console
    $ cd /var/www/servembtiles
    $ git clone GIT_REPOSTIORY_URL repo
    ```

3. Activate *venv* and install requirements:

    ```console
    $ source bin/activate
    (servembtiles)$ cd repo
    (servembtiles)$ pip install -r requirements.txt
    ```

4. Symlink the 'servembtiles_nginx.conf' to */etc/nginx/sites-enabled/*

    ```console
    $ sudo ln -s /var/www/servembtiles/repo/conf/servembtiles_cache.conf /etc/nginx/sites-enabled/
    $ sudo ln -s /var/www/servembtiles/repo/conf/servembtiles_nginx.conf /etc/nginx/sites-enabled/
    $ sudo ln -s /var/www/servembtiles/repo/conf/servembtiles_cache_nginx.conf /etc/nginx/sites-enabled/
    ```


5. To allow the socket (for uwsgi<->nginx comunication) to be created, chmod on servembtiles/repo directory:

    ```console
    sudo chmod 777 /var/www/servembtiles/repo
    ```

6. Copy upstart configuration file, *servembtiles-uwsgi.conf* to /etc/init to run application as a service:

    ```console
    sudo cp /var/www/servembtiles/repo/servembtiles-uwsgi.conf /etc/init
    ```

7. Copy Map Data (or configure settings.py to a location which the nginx user can access)

    ```console
    $ mkdir /var/www/servembtiles/servembtiles/mapdata
    $ cp [MAPDATA.mbtiles] /var/www/servembtiles/repo/mapdata
    ```


8. Start uwsgi application & Restart nginx

    ```console
    sudo service servembtiles-uwsgi start
    sudo service nginx restart
    ```

    > Note: Related log files are located in "/var/log/nginx" & "/var/log/uwsgi/servembtiles-uwsgi.log"
    > Application configured to be served at SERVER_IP_ADDRESS:8005
    > *Port configured in servembtiles_nginx.conf file*
