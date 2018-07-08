import pickle
import utm
from pyproj import Proj

class Map(object):
    def __init__(self, lat, lng, x_resolution, y_resolution, size_x, size_y, proj, pixel_to_km, GSD, x1, y1, x2, y3):
        self.lat = lat
        self.lng = lng
        self.x_resolution = x_resolution 
        self.y_resolution = y_resolution
        self.size_x = size_x
        self.size_y = size_y
        # self.psize_x = size_x * resolution
        # self.proj = proj
        cx, cy, z_no, z_r = utm.from_latlon(lat, lng)
        self.z_r = z_r
        self.z_no = z_no
        self.proj = Proj(proj='utm', zone=self.z_no, ellps='WGS84')
        # print proj(lng, lat)
        self.bounds = (
            x1,
            y1,
            x2,
            y3
            )

        w, s = utm.to_latlon(self.bounds[0], self.bounds[1], z_no, z_r)
        e, n = utm.to_latlon(self.bounds[2], self.bounds[3], z_no, z_r)
        # print self.bounds, cx, cy
        self.ll_bounds = (s, w, n, e)
        # print self.ll_bounds

    def _latLngToIndex(self, lat, lng):
        # print type(lat), type(lng)
        x, y, _temp1, _temp2 = utm.from_latlon(lat, lng)
        return (
            (x - self.bounds[0]) / self.psize * self.size,
            (y - self.bounds[1]) / self.psize * self.size)

    def save(self, f):
        pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load(f):
        return pickle.load(f)
