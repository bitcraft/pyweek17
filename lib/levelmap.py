from array import array
from math import hypot
from itertools import product

from const import colors, TILESIZE
from euclid import Point2



def pack(a, b):
    return (a << 4) | b

def unpack(a):
    return (a >> 4) & 0x0F, a & 0x0F

def distance2((ax, ay), (bx, by)):
    return hypot((ax - bx), (ay - by))


class LevelMap:
    def __init__(self, dim):
        self.height, self.width = dim
        self.data = []
        self.colors = colors
        self.tile_size = TILESIZE
        self.renderer = None

        [ self.data.append(array('B')) for i in xrange(self.height) ]
        for (y, x) in product(xrange(self.height), xrange(self.width)):
            self.data[y].append(0)

    def set_renderer(self, r):
        self.renderer = r

    def set_tile(self, (x, y), t, v=0):
        self.data[y][x] = pack(t, v)
        if self.renderer:
            self.renderer.mark_changed((x, y))

    def get_tile(self, (x, y)):
        return unpack(self.data[y][x])

    def test_type(self, (x, y), t):
        return t == unpack(self.data[y][x])[0]

    def tiles_of_type(self, types):
        assert isinstance(types, (list, tuple))
        for y, row in enumerate(self.data):
            for x, value in enumerate(row):
                if unpack(value)[0] in types:
                    yield (x, y)

    def get_tile_color(self, (x, y)):
        try:
            return self.colors[self.data[y][x]]
        except:
            return (255,255,255)
    
    def nearest_tile(self, origin, types, blacklist=None):
        nearest = (None, 9999999999999)
        origin = origin[0], origin[1]

        for position in self.tiles_of_type(types):
            d = distance2(position, origin)
            if d < nearest[1] and position not in blacklist:
                nearest = position, d

        return (Point2(*nearest[0]), nearest[1]) if nearest[0] else (None, None)

