#!/usr/bin/env python3
"""
mbtiles WSGI application

MBTiles is a specification for storing tiled map data in SQLite databases for immediate usage and for transfer.
From:
https://github.com/mapbox/mbtiles-spec
"""
import os
import json
import sqlite3
import mimetypes
import logging
from wsgiref.util import shift_path_info

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

MBTILES_ABSFILEPATH = os.environ.get('MBTILES_ABSFILEPATH')  # or set this statically
MBTILES_TILE_EXT = os.environ.get("MBTILES_TILE_EXT", '.png')

class MBTilesFileNotFound(Exception):
    pass

class UnsupportedMBTilesVersion(Exception):
    pass

class MBTilesApplication:
    """
    Serves rendered tiles within the given .mbtiles (sqlite3) file.

    Refer to the MBTiles specification at:
    https://github.com/mapbox/mbtiles-spec
    """

    def __init__(self, mbtiles_filepath, tile_image_ext='.png'):
        if not os.path.exists(mbtiles_filepath):
            raise MBTilesFileNotFound(mbtiles_filepath)

        self.mbtiles_filepath = mbtiles_filepath
        self.tile_image_ext = tile_image_ext
        self.tile_content_type = mimetypes.types_map[tile_image_ext.lower()]
        self.maxzoom = None
        self.minzoom = None

        self._check_mbtiles_version()
        self._populate_supported_zoom_levels()

    def _check_mbtiles_version(self):
        """
        Check metadata table for version
        :return: None
        """
        version_query = 'SELECT value from metadata WHERE name = "version";'
        with sqlite3.connect(self.mbtiles_filepath) as connection:
            cursor = connection.cursor()
            cursor.execute(version_query)
            version_result = cursor.fetchone()[0]
        major, minor, point = [int(i) for i in version_result.split('.')]
        if not (major == 1 and minor <= 2):
            raise UnsupportedMBTilesVersion("Unknown MBTiles version({}) (if 'tiles' and 'metadata' tables are unchnaged update this to support the new version. 'grids' not supported!)".format(version_result))

    def _populate_supported_zoom_levels(self):
        """
        Query the metadata table and obtain max/min zoom levels
        :return: None
        """
        query = 'SELECT name, value FROM metadata WHERE name="minzoom" OR name="maxzoom";'
        with sqlite3.connect(self.mbtiles_filepath) as connection:
            cursor = connection.cursor()
            cursor.execute(query)
        # add maxzoom, minzoom to instance
        for name, value in cursor.fetchall():
            setattr(self, name.lower(), int(value))

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'GET':
            uri_field_count = len(environ['PATH_INFO'].split('/'))
            base_uri = shift_path_info(environ)

            # handle 'metadata' requests
            if base_uri == 'metadata':
                query = 'SELECT * FROM metadata;'
                with sqlite3.connect(self.mbtiles_filepath) as connection:
                    cursor = connection.cursor()
                    cursor.execute(query)
                    metadata_results = cursor.fetchall()
                if metadata_results:
                    status = '200 OK'
                    response_headers = [('Content-type', 'application/json')]
                    start_response(status, response_headers)
                    json_result = json.dumps(metadata_results)
                    return [json_result.encode("utf8"),]
                else:
                    status = '404 NOT FOUND'
                    response_headers = [('Content-type', 'text/plain')]
                    start_response(status, response_headers)
                    return ['"metadata" not found in configured .mbtiles file!', ]

            # handle tile request
            elif uri_field_count >= 3:  # expect:  zoom, x & y
                try:
                    zoom = int(base_uri)
                    if all((self.minzoom, self.maxzoom)) and not (self.minzoom <= zoom <= self.maxzoom):
                        status = "400 Bad Request"
                        response_headers = [('Content-type', 'text/plain')]
                        start_response(status, response_headers)
                        return ['zoomlevel({}) not in valid range minzoom({}) maxzoom({}) PATH_INFO: {}'.format(zoom,
                                                                                                                self.minzoom,
                                                                                                                self.maxzoom,
                                                                                                                environ['PATH_INFO'])]
                    x = int(shift_path_info(environ))
                    y, ext = shift_path_info(environ).split('.')
                    y = int(y)
                except ValueError as e:
                    status = "400 Bad Request"
                    response_headers = [('Content-type', 'text/plain')]
                    start_response(status, response_headers)
                    return ['Unable to parse PATH_INFO({}), expecting "z/x/y.(png|jpg)"'.format(environ['PATH_INFO']), e.args()]

                query = 'SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?;'
                values = (zoom, x, y)
                with sqlite3.connect(self.mbtiles_filepath) as connection:
                    cursor = connection.cursor()
                    cursor.execute(query, values)
                    tile_results = cursor.fetchone()

                if tile_results:
                    tile_result = tile_results[0]
                    status = '200 OK'
                    response_headers = [('Content-type', self.tile_content_type)]
                    start_response(status, response_headers)
                    return [tile_result,]
                else:
                    status = '404 NOT FOUND'
                    response_headers = [('Content-type', 'text/plain')]
                    start_response(status, response_headers)
                    return ['No data found for request location: {}'.format(environ['PATH_INFO'])]

        status = "400 Bad Request"
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return ['request URI not in expected: ("metadata", "/z/x/y.png")', ]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve",
                        default=False,
                        action='store_true',
                        help="Start tset server")
    parser.add_argument('-p', '--port',
                        default=8005,
                        type=int,
                        help="Test server port [DEFAULT=8005]")
    parser.add_argument('-a', '--address',
                        default='localhost',
                        help='Test address to serve on [DEFAULT="localhost"]')
    parser.add_argument('-f', '--filepath',
                        default=MBTILES_ABSFILEPATH,
                        required=True,
                        help="mbtiles filepath [DEFAULT={}]\n(Defaults to enviornment variable, 'MBTILES_ABSFILEPATH')".format(MBTILES_ABSFILEPATH))
    parser.add_argument('-e', '--ext',
                        default=MBTILES_TILE_EXT,
                        help="mbtiles image file extention [DEFAULT={}]\n(Defaults to enviornment variable, 'MBTILES_TILE_EXT')".format(MBTILES_TILE_EXT))
    args = parser.parse_args()
    args.filepath = os.path.abspath(args.filepath)
    if args.serve:
        # create console handler and set level to debug
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logger.addHandler(console)
        logger.setLevel(logging.DEBUG)

        logger.info("FILEPATH: {}".format(args.filepath))
        logger.info("TILE EXT: {}".format(args.ext))
        logger.info("ADDRESS : {}".format(args.address))
        logger.info("PORT    : {}".format(args.port))
        from wsgiref.simple_server import make_server
        mbtiles_app = MBTilesApplication(mbtiles_filepath=args.filepath, tile_image_ext=args.ext)
        server = make_server(args.address, args.port, mbtiles_app)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("stopped.")
    else:
        logger.warn("'--serve' option not given!")
        logger.warn("\tRun with the '--serve' option to serve tiles with the test server.")