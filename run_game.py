import pygame
import array
import random
import tilemap
import context
import math
import heapq
import collections
from itertools import product
from euclid import Vector2, Point2, Point3, Vector3, Matrix4

from pygame.locals import *

colors = [
    '#191e18',
    '#75987c',
    '#403d32',
    '#ef899b',
    '#3f9089',
    '#75202d',
    '#09303a',
    '#bc9e60',
    '#f7a50d',
    '#403e30',
    '#a2000d',
    '#e0e2e0',
    '#f9f9f0',
]

colors = [ pygame.Color(i) for i in colors ]

TILESIZE = 48
TIMESTEP = 30.0

REGOLITH = 2
EXCAVATED = 3
STOCKPILE = 4


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

class LevelMap:
    def __init__(self, dim):
        self.height, self.width = dim
        self.data = []
        self.colors = colors
        self.tile_size = TILESIZE
        self.changed = True

        # initialize level data array with 1
        [ self.data.append(array.array('B')) for i in xrange(self.height) ]
        for (y, x) in product(xrange(self.height), xrange(self.width)):
            self.data[y].append(REGOLITH)
            #self.data[y].append(random.randint(0, 10))

    def tiles_of_type(self, tile_type):
        for y, row in enumerate(self.data):
            for x, value in enumerate(row):
                if value == tile_type:
                    yield (x, y)

    def nearest_tile(self, origin, tile_type, blacklist=None):
        nearest = (None, 9999999999999)
        origin = origin[0], origin[1]

        for position in self.tiles_of_type(tile_type):
            d = distance2(position, origin)
            if d < nearest[1] and position not in blacklist:
                nearest = position, d

        return (Point2(*nearest[0]), nearest[1]) if nearest[0] else (None, None)


class AIContext(context.Context):
    def update(self, time):
        pass


class ShuttleFlyAI(AIContext):
    def enter(self):
        self.sprite.move_vector = Vector3(0,0,.02/TIMESTEP)

    def update(self, time):
        self.sprite.position += self.sprite.move_vector * time

    def exit(self):
        self.sprite.move_vector = Vector3(0,0,0)


class MoveRandomAI(AIContext):
    def update(self, time):
        self.sprite.position += self.sprite.move_vector * time
        if random.random() > .90:
            s = self.sprite.travel_speed
            self.sprite.move_vector = Vector3(
                random.uniform(-s, s),
                random.uniform(-s, s),
                0)


class ExcavateAI(AIContext):
    complete = 5000.0

    def update(self, time):
        self._progress += time
        self.progress = self._progress / ExcavateAI.complete

        if self.progress >= 1.0:
            x, y, z = map(int, self.sprite.position)
            self.sprite.level.data[y][x] = EXCAVATED
            self.sprite.carried += 1
            player.tilechange = 1
            self.done()

    def enter(self):
        x, y, z = map(int, self.sprite.position)
        if not self.sprite.level.data[y][x] == REGOLITH:
            self.done()

        self._progress = 0.0
        self.progress = 0.0

class SearchAndTravelAI(AIContext):
    keys = collections.defaultdict(list)

    def update(self, time):
        spr = self.sprite

        if not self.path:
            self.plan()

            if not self.path:
                self.done()
                return

        n = spr.position - self.path[-1] - (.5, .5, 0)
        if abs(n) < .05:
            self.path.pop()
            if len(self.path) == 0:
                spr.move_vector = Vector3(0,0,0)
                self.done()
                return

        spr.move_vector = n.normalize()
        spr.position -= spr.move_vector * spr.travel_speed

    def plan(self):
        spr = self.sprite

        if self.my_key is None:
            blacklist = []
        else:
            blacklist = SearchAndTravelAI.keys[self.my_key]
        self.dest, dist = spr.level.nearest_tile(spr.position, self.tile_type, blacklist)

        if self.dest is not None:
            self.path = aStar(tuple(map(round, spr.position[:2])), tuple(self.dest), (20, 20))
            SearchAndTravelAI.keys[self.my_key].append(tuple(self.dest))

    def enter(self):
        self.path = None
        self.my_key = getattr(self, "key", None)


class DropCarriedAI(AIContext):
    def update(self, tile):
        spr = self.sprite
        if spr.carried > 0:
            x, y = map(int, spr.position)[:2]

            if spr.level.data[y][x] == STOCKPILE:
                spr.carried -= 1
                player.regolith += 1
            else:
                self.done()
        else:
            #s = Shuttle(spr.level)
            #s.position = spr.position.copy()
            #spr.groups()[0].add(s)
            self.done()


class GameObject(pygame.sprite.Sprite):
    def __init__(self, level):
        super(GameObject, self).__init__()
        self.travel_speed = 3/TIMESTEP
        self.level = level
        self.ai_stack = context.ContextDriver()
        self.ai_lists = []
        self.ai_cursor = 0 
        self.move_vector = Vector3(0,0,0)
        self.position = Vector3(0,0,0)
        self.init()

        self.pixel_size = self.world_size * TILESIZE

        for task in reversed(self.ai_lists[0]):
            self.ai_stack.append(task)

    def update(self, time):
        task = self.ai_stack.current_context
        if task:
            task.update(time)
        else:
            self.ai_stack = context.ContextDriver()
            for task in reversed(self.ai_lists[0]):
                self.ai_stack.queue(task)

class Harvester(GameObject):
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill((random.randint(64, 255), random.randint(64, 255), random.randint(64, 255)))
        self.world_size = Vector2(.1, .5)
        self.carried = 0

        self.ai_lists.append([
            SearchAndTravelAI(sprite=self, tile_type=REGOLITH, key=REGOLITH),
            ExcavateAI(sprite=self),
            SearchAndTravelAI(sprite=self, tile_type=STOCKPILE),
            DropCarriedAI(sprite=self)
        ])

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
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[4])
        self.world_size = Vector2(.2, .5)

class Shuttle(GameObject):
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[-1])
        self.world_size = Vector2(.2, .5)
        self.ai_lists.append([ShuttleFlyAI(sprite=self)])


class IsoGroup(pygame.sprite.Group):
    def update(self, time):
        self.tilemap.update(time)
        super(IsoGroup, self).update(time)

    def set_tilemap(self, tilemap, tile_size):
        self.tilemap = tilemap
        self.tile_size = tile_size

    def draw(self, surface, area):
        sprites = self.sprites()

        self.tilemap.draw(surface, area, sprites)

        for s in sprites:
            p = getattr(s.ai_stack.current_context, "progress", None)
            if p:
                point = self.tilemap.project_point(s.position + (0,0,1))
                point = map(int, point[:2])
                small_progress(surface, colors[REGOLITH-1], colors[-2], point, p)


class Player:
    energy = 0
    regolith = 0
    tilechange = 0

player = Player()


def draw_bar(s, c1, c2, r, v):
    s.fill(c1, r)
    s.fill(c2, (r.topleft, (r.w, r.h-r.h*v)))

def small_progress(s, c1, c2, point, v):
    x = math.ceil(28.0*v)
    if x > 28: x = 28
    s.fill(c2, (point, (30, 8)))
    s.fill(c1, (point[0]+1, point[1]+1, x, 6))

if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode(screen_dim)

    font = pygame.font.Font(pygame.font.get_default_font(), 12)

    level = LevelMap((20, 20))

    level.data[4][4] = STOCKPILE
    level.data[16][16] = STOCKPILE
    level.data[4][16] = STOCKPILE
    level.data[16][4] = STOCKPILE

    tilemap = tilemap.TilemapRenderer([level], TILESIZE)

    game_group = IsoGroup()
    game_group.set_tilemap(tilemap, TILESIZE)

    for i in xrange(10):
        h = Harvester(level)
        h.position = Vector3(random.uniform(0,20), random.uniform(0,20), 0)
        game_group.add(h)

    area = pygame.Rect((0,0), screen_dim)

    for i, c in enumerate(colors):
        screen.fill(c, (i*32+10,10,32,32))
        screen.blit(font.render(str(i+1), 1, (255,255,255)), (i*32+20, 44))

    run = True
    while run:
        game_group.update(30)

        if player.tilechange:
            game_group.tilemap.changed = True
            player.tilechange = False
            screen.fill((0,0,0))

        game_group.draw(screen, area)

        draw_bar(screen, colors[-4], colors[-2], Rect(10, 60, 32, 128), player.energy / 50.0)
        draw_bar(screen, colors[REGOLITH-1], colors[-2], Rect(48, 60, 32, 128), player.regolith / 50.0)

        pygame.display.flip()

        try:
            event = pygame.event.poll()
            #event = pygame.event.wait()
            if event.type == QUIT: run = False
            if event.type == MOUSEMOTION:
                mx, my = event.pos
                x, y, z = game_group.tilemap.unproject_point(Vector3(mx, my, 0))

        except KeyboardInterrupt:
            run = False

