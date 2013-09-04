import pygame
import array
import random
import tilemap
import context
import math
import heapq
from itertools import product
from euclid import Point2, Vector2, Vector3, Matrix4

from pygame.locals import *

colors = [
    '#ef899b',
    '#09303a',
    '#bc9e60',
    '#f7a50d',
    '#3f9089',
    '#75202d',
    '#403e30',
    '#a2000d',
    '#75987c',
    '#191e18',
    '#e0e2e0',
    '#f9f9f0',
]

colors = [ pygame.Color(i) for i in colors ]

TILESIZE = 48
MATERIALS = 2
TIMESTEP = 30.0

screen_dim = (1200, 800)

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

    def retracePath(c):
        path = [c]
        while parent.get(c, None) is not None:
            c = parent[c]
            path.append(c)
        path.reverse()
        return path

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

class LevelMap:
    def __init__(self, dim):
        self.height, self.width = dim
        self.data = []
        self.colors = colors
        self.tile_size = TILESIZE
        self.changed = True
        nearest_cache = {}

        [ self.data.append(array.array('B')) for i in xrange(self.height) ]

        for (y, x) in product(xrange(self.height), xrange(self.width)):
            self.data[y].append(random.randint(0,10))

    def mark_changed(self):
        self.nearest_cache = {}

    def tiles_of_type(self, tile_type):
        for y, row in enumerate(self.data):
            for x, value in enumerate(row):
                if value == tile_type:
                    yield (x, y)

    def nearest_tile(self, origin, tile_type):
        nearest = (None, 9999999999999)
        origin = origin[0], origin[1]

        for position in self.tiles_of_type(tile_type):
            d = distance2(position, origin)
            if d < nearest[1]:
                nearest = position, d

        return (Point2(*nearest[0]), nearest[1]) if nearest[0] else (None, None)


class AIContext(context.Context):
    def update(self, time):
        pass


class MoveRandomAI(AIContext):
    def update(self, time):
        self.sprite.position += self.sprite.move_vector * time
        if random.random() > .90:
            s = self.sprite.travel_speed
            self.sprite.move_vector = Vector2(
                random.uniform(-s, s),
                random.uniform(-s, s))


class MoveToMaterialsAI(AIContext):
    def update(self, time):
        dest, dist = self.sprite.level.nearest_tile(self.sprite.position, MATERIALS)

        if dest:
            path = aStar(tuple(map(round, self.sprite.position)), tuple(dest), (20, 20))
        else:
            global MATERIALS
            MATERIALS += 1
            return

        x, y = map(int, self.sprite.position)
        if self.sprite.level.data[y][x] == MATERIALS:
            self.sprite.level.data[y][x] = 0

        if path:
            s = self.sprite.travel_speed
            n = self.sprite.position - path.pop()
            if len(path) == 2:
                n += (.5, .5)
            self.sprite.move_vector = Vector2(*clip(list(n), (-s, -s), (s, s)))
            self.sprite.position -= self.sprite.move_vector * time

class GameObject(pygame.sprite.Sprite):
    def __init__(self, level):
        super(GameObject, self).__init__()
        self.travel_speed = .5/TIMESTEP
        self.level = level
        self.ai_stack = context.ContextDriver()
        self.move_vector = Vector2(0,0)
        self.position = Vector2(0,0)
        self.init()

        self.pixel_size = self.world_size * TILESIZE

    def update(self, time):
        try:
            self.ai_stack.current_context.update(time)
        except:
            raise
            pass

class Harvester(GameObject):
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[-1])
        self.world_size = Vector2(.1, .5)


class Turret(GameObject):
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[2])
        self.world_size = Vector2(.2, .5)

class Minion(GameObject):
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[3])
        self.world_size = Vector2(.2, .5)

class Enemy(GameObject):
    def __init__(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[4])
        self.world_size = Vector2(.2, .5)

    def update(self, time):
        pass


class IsoGroup(pygame.sprite.Group):
    def update(self, time):
        self.tilemap.update(time)
        super(IsoGroup, self).update(time)

    def set_tilemap(self, tilemap, tile_size):
        self.tilemap = tilemap
        self.tile_size = tile_size

    def draw(self, surface, area):
        sprites = []
        for spr in self.sprites():
            sprites.append((1, spr))
        self.lostsprites = []

        self.tilemap.draw(surface, area, sprites)

if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode(screen_dim)

    level = LevelMap((20, 20))
    tilemap = tilemap.TilemapRenderer([level], TILESIZE)

    h00 = Harvester(level)

    #h00.ai_stack.append(MoveRandomAI(sprite=h00))
    h00.ai_stack.append(MoveToMaterialsAI(sprite=h00))
    h00.position += 4.5, 4.5

    game_group = IsoGroup()
    game_group.set_tilemap(tilemap, TILESIZE)
    game_group.add(h00)

    area = pygame.Rect((0,0), screen_dim)

    run = True
    while run:
        game_group.update(30)

        screen.fill((0,0,0))
        game_group.draw(screen, area)
        pygame.display.flip()

        try:
            event = pygame.event.poll()
            #event = pygame.event.wait()
            if (event.type == QUIT) or (event.type == KEYDOWN): run = False
            if event.type == MOUSEMOTION:
                mx, my = event.pos

                x, y, z = game_group.tilemap.unproject_point(Vector3(mx, my, 0))
                try:
                    level.data[int(y)][int(x)] = 0
                except IndexError:
                    pass

        except KeyboardInterrupt:
            run = False

