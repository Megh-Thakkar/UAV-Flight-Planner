#!/usr/bin/python
from os import path
from pyproj import Proj
import numpy
from srtm import VTPTile
from PIL import Image, ImageDraw
import json
import utm
from map import Map
import numpy as np

class HeightMap(Map):
    def __init__(self, lat, lng, x_resolution, y_resolution, size_x, size_y, proj, pixel_to_km, GSD, x1, y1, x2, y3):
        Map.__init__(self, lat, lng, x_resolution, y_resolution, size_x, size_y, proj, pixel_to_km, GSD, x1, y1, x2, y3)
        self.heights = numpy.zeros((size_y, size_x), dtype=float)

    def to_image(self):
        data = self.heights
        rescaled = (255.0 / data.max() * (data - data.min())).astype(numpy.uint8)
        return Image.fromarray(rescaled).transpose(Image.FLIP_TOP_BOTTOM)

class OSMHeightMap(HeightMap):
    def __init__(self, lat, lng, resolution, size, proj, f):
        HeightMap.__init__(self, lat, lng, resolution, size, proj)

        img = Image.new('F', (size, size))
        draw = ImageDraw.Draw(img)
        fc = json.load(f)
        for f in fc['features']:
            h = float(f['properties']['height']) if f['properties'].has_key('height') else 10
            # print h
            if type(f['geometry']['coordinates'][0]) == float:
                continue
            elif type(f['geometry']['coordinates'][0]) == list and type(f['geometry']['coordinates'][0][0]) == float:
                # print '0\n'
                # print f['geometry']['coordinates'][0]
                coords = map(lambda ll: self._latLngToIndex(ll[1], ll[0]), f['geometry']['coordinates'])
            elif type(f['geometry']['coordinates'][0]) == list and type(f['geometry']['coordinates'][0][0]) == list and type(f['geometry']['coordinates'][0][0][0]) == float:
                # print '1\n'
                coords = map(lambda ll: self._latLngToIndex(ll[1], ll[0]), f['geometry']['coordinates'][0])
            elif type(f['geometry']['coordinates'][0][0][0]) == list and type(f['geometry']['coordinates'][0][0][0][0]) == float:
                # print '2\n'
                coords = map(lambda ll: self._latLngToIndex(ll[1], ll[0]), f['geometry']['coordinates'][0][0])
            # print coords
            draw.polygon(coords, fill=h)

        self.heights = numpy.array(img)

class SrtmHeightMap(HeightMap):
    def __init__(self, lat, lng, x_resolution, y_resolution, proj, pixel_to_km, GSD, x1, y1, x2, y3, data_dir):
        self.data_dir = data_dir
        # for y in xrange(0, size_y):
        #     cy = self.bounds[1] + y / float(size) * self.psize
        #     for x in xrange(0, size_x):
        #         cx = self.bounds[0] + x / float(size) * self.psize
        #         lat, lng = utm.to_latlon(cx, cy, self.z_no, self.z_r)

        #         tile_key = SrtmHeightMap._tileKey(lat, lng)
        #         if not tiles.has_key(tile_key):
        #             tiles[tile_key] = SrtmHeightMap._loadTile(data_dir, lat, lng)
        #             print 'Loaded tile', tile_key
                
        #         v = tiles[tile_key].getAltitudeFromLatLon(lat, lng)
                # print lat, lng, v
        per_X = GSD * x_resolution * pixel_to_km
        per_Y = GSD * y_resolution * pixel_to_km
        size_x = int((x2 - x1) / per_X) - 1
        size_y = int((y3 - y1) / per_Y) - 1
        lx = np.linspace(x1, x2, int((x2 - x1) / per_X))
        ly = np.linspace(y1, y3, int((y3 - y1) / per_Y))
        kx, ky = np.meshgrid(lx, ly)
        # print kx 
        # print ky
        # print size_x, size_y
        HeightMap.__init__(self, lat, lng, x_resolution, y_resolution, size_x, size_y, proj, pixel_to_km, GSD, x1, y1, x2, y3)
        tiles = {}
        for i in range(0, len(kx) - 1):
            y = (ky[i][0] + ky[i + 1][0]) / 2.00
            for j in range(0, len(kx[i]) - 1):
                centre = (kx[i][j] + kx[i][j + 1]) / 2.00
                # centres.append({'X': centre, 'Y': y})
                lat, lng = utm.to_latlon(centre, y, self.z_no, self.z_r)
                tile_key = SrtmHeightMap._tileKey(lat, lng)
                if not tiles.has_key(tile_key):
                    tiles[tile_key] = SrtmHeightMap._loadTile(data_dir, lat, lng)
                    # print 'Loaded tile', tile_key
                v = tiles[tile_key].getAltitudeFromLatLon(lat, lng)
                self.heights[i,j] = v
        # print size_y, size_x
        
    @staticmethod
    def _tileKey(lat, lng):
        return '%s%02d%s%03d.hgt' % (
            'N' if lat >= 0 else 'S',
            int(lat),
            'E' if lng >= 0 else 'W',
            int(lng))

    @staticmethod
    def _loadTile(data_dir, lat, lng):
        p = path.join(data_dir, SrtmHeightMap._tileKey(lat, lng))
        # print str(p)
        with open(p, 'rb') as f:
            return VTPTile(f, int(lat), int(lng))

# if __name__ == '__main__':
#     import argparse

#     parser = argparse.ArgumentParser()
#     parser.add_argument('center', type=float, nargs=2, help='Map center latitude ang longitude')
#     parser.add_argument('resolution', type=float, help='Resolution (m/pixel)')
#     parser.add_argument('size', type=int, help='Map size in pixels')
#     parser.add_argument('--projection', type=str, default='epsg:3006', help='Projection name (for example "epsg:3006")')
#     parser.add_argument('--output', type=str, default=None, help='Output path/filename')
#     parser.add_argument('--save-image', type=str, default=None, help='Image output path/filename')
#     parser.add_argument('--elevation-dir', type=str, default='data', help='Directory path to find elevation .hgt files')
#     parser.add_argument('--geojson', type=str, required=True, help='Path for buildings GeoJSON')

#     args = parser.parse_args()

#     lat = float(args.center[0])
#     lng = float(args.center[1])
#     resolution = float(args.resolution)
#     size = int(args.size)
#     print size, resolution
#     proj = Proj(init=args.projection)

#     elev = SrtmHeightMap(self, lat, lng, x_resolution, y_resolution, size_x, size_y, proj, pixel_to_km, GSD, x1, y1, x2, y3, args.elevation_dir)
#     with open(args.geojson, 'r') as f:
#         buildings = OSMHeightMap(lat, lng, resolution, size, proj, f)

#     hm = HeightMap(lat, lng, resolution, size, proj)
#     hm.heights = elev.heights + buildings.heights

#     if args.save_image:
#         hm.to_image().save(args.save_image)

#     if args.output:
#         with open(args.output, 'wb') as f:
#             hm.save(f)
