servembtiles.py
================

'servembtiles.py' is a pure python3 wsgi application for serving [MBTiles](https://github.com/mapbox/mbtiles-spec).
MBTiles can be exported from [Tilemill](https://www.mapbox.com/tilemill/).  (If you do web-maps you should checkout tilemill)

The application's MBTiles filepath can be defined by the environment variable, "MBTILES_ABSFILEPATH".
The application's tile image file extension can also be set via the environment variable, "MBTILES_TILE_EXT" (defaulting to '.png').

This includes a simple test server for verification purposes.
Ideally, this should probably be served via [Nginx](http://nginx.com/resources/glossary/reverse-proxy-server/) or apache2, with reverse proxy caching.

If I get some time I'll add these configuration steps.

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

