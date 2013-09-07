import heapq
import math
from euclid import Point3


def distance2((ax, ay), (bx, by)):
    return math.hypot((ax - bx), (ay - by))

def clip(vector, lowest, highest):
    return type(vector)(map(min, map(max, vector, lowest), highest))

"""
modified from:
http://stackoverflow.com/questions/4159331/python-speed-up-an-a-star-pathfinding-algorithm
"""
def aStar(current, end, limit):
    parent = {}
    openHeap = []
    openSet = set()
    closedSet = set()

    def surrounding((x, y)):
        return [ clip(i, (0,0), limit) for i in ((x-1, y-1), (x-1, y), (x-1, y+1), (x, y-1), (x, y+1),
                (x+1, y-1), (x+1, y), (x+1, y+1)) ]
        #return [ clip(i, (0,0), limit) for i in ((x-1, y), (x, y-1), (x+1, y), (x, y+1)) ]

    def retracePath(c):
        path = [Point3(c[0], c[1], 0)]
        while parent.get(c, None) is not None:
            c = parent[c]
            path.append(Point3(c[0], c[1], 0))
        return path

    current = current[0], current[1]
    openSet.add(current)
    openHeap.append((0,current))
    while openSet:
        current = heapq.heappop(openHeap)[1]
        if current == end:
            return retracePath(current)
        openSet.remove(current)
        closedSet.add(current)
        for tile in surrounding(current):
            if tile not in closedSet:
                if tile not in openSet:
                    openSet.add(tile)
                    heapq.heappush(openHeap, (distance2(tile, end),tile))
                parent[tile] = current
    return []
