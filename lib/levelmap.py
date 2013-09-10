from array import array
from math import hypot
from itertools import product
from collections import defaultdict
from heapq import heappush, heappop
import math
import time

from euclid import Point2, Point3, Vector3



def pack(a, b):
    return (a << 4) | b

def unpack(a):
    return (a >> 4) & 0x0F, a & 0x0F

def distance2((ax, ay), (bx, by)):
    return hypot((ax - bx), (ay - by))


class LevelMap:
    def __init__(self, dim, seed=0):
        self.height, self.width = dim
        self.data = []
        self.renderer = None
        self.totals = defaultdict(int)
        self.scan_cache = {}

        [ self.data.append(array('B')) for i in xrange(self.height) ]
        for (y, x) in product(xrange(self.height), xrange(self.width)):
            self.data[y].append(pack(seed,0))

    def set_renderer(self, r):
        self.renderer = r

    def set_tile(self, (x, y), t, v=0):
        ot, ov = unpack(self.data[y][x])
        if not ot == 0:
            self.totals[ot] -= 1
        self.totals[t] += 1
        self.data[y][x] = pack(t, v)
        if self.renderer:
            self.renderer.mark_changed((x, y))
        self.scan_cache = {}

    def get_total(self, tile_type):
        return self.totals[tile_type]

    def get_tile(self, (x, y)):
        return unpack(self.data[y][x])

    def get_raw(self, (x, y)):
        return self.data[y][x]

    def test_type(self, (x, y), t):
        return t == unpack(self.data[y][x])[0]

    def tiles_of_type(self, types):
        assert isinstance(types, (list, tuple, set))
        for y, row in enumerate(self.data):
            for x, value in enumerate(row):
                if unpack(value)[0] in types:
                    yield x, y

    def nearest_tiles(self, origin, types, blacklist=[]):
        """ return a heap of tiles closest to a origin """
        origin = origin[0], origin[1]
        dx, dy = origin[0] - int(origin[0]), origin[1] - int(origin[1])
        heap = []

        nearest = (None, 9999999999999)
        for tx, ty in self.tiles_of_type(types):
            if (tx, ty) not in blacklist:
                p = (tx + dx,  ty + dy)
                heappush(heap, (distance2(p, origin), p))

        return heap

    def pathfind_type(self, current, targets, blacklist, impassable=None):
        """ pathfind to a tile type """

        possible = self.nearest_tiles(current, targets, blacklist)
        if not possible:
            return [], True

        path = []
        complete = True
        start_time = time.time()
        while possible:
            if time.time() - start_time > .05:
                return path, complete
            position = heappop(possible)[1]
            path, complete = self.pathfind(current, position, [], impassable)
            if path:
                return path, complete

        return [], True

    def pathfind(self, current, end, blacklist, impassable=None):
        """ modified: http://stackoverflow.com/questions/4159331/python-speed-up-an-a-star-pathfinding-algorithm """

        def clip(vector, lowest, highest):
            return type(vector)(map(min, map(max, vector, lowest), highest))

        def surrounding_clip((x, y), limit):
            return [ clip(i, (0,0), limit) for i in ((x-1, y-1), (x-1, y), (x-1, y+1), (x, y-1), (x, y+1), (x+1, y-1), (x+1, y), (x+1, y+1)) ]

        def surrounding_noclip((x, y), limit):
            return (x-1, y-1), (x-1, y), (x-1, y+1), (x, y-1), (x, y+1), (x+1, y-1), (x+1, y), (x+1, y+1)

        def retracePath(c):
            path = [c]
            while parent.get(c, None) is not None:
                c = parent[c]
                path.append(c)
            return path

        start_time = time.time()

        parent = {}
        openHeap = []
        openSet = set()
        closedSet = set()
        limit = self.width-1, self.height-1

        surrounding = surrounding_clip

        current = current[0], current[1]
        openSet.add(current)
        openHeap.append((0,current))
        while openSet:
            if time.time() - start_time > .0125:
                try:
                    return retracePath(current), False
                except:
                    return [], True

            current = heappop(openHeap)[1]

            if map(int, current) == map(int, end):
                return retracePath(current), True

            openSet.remove(current)
            closedSet.add(current)
            for tile in surrounding(current, limit):
                try:
                    if self.get_tile(map(int, tile))[0] == impassable:
                        continue
                except IndexError:
                    pass

                if tile not in closedSet:
                    parent[tile] = current
                    if tile not in openSet:
                        openSet.add(tile)
                        heappush(openHeap, (distance2(tile, end),tile))

        return [], True

    def scan_block(self):
        """ search for a 5x5 block """

        def scan_row(x, y):
            try:
                return self.scan_cache[(x, y)]
            except KeyError:
                for i in xrange(x, x+5):
                    tile, value = self.get_tile((i, y))
                    if not tile == 0:
                        self.scan_cache[(x, y)] = False
                        return False
                cache[(x, y)] = True
                return True

        for y, x in product(xrange(self.height-5), xrange(self.width-5)):
            for i in xrange(y, y+5):
                found = scan_row(x, i)
                if not found: 
                    break

            if found:
                return x, y

        return None
