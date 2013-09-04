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
    '#191e18',
    '#e0e2e0',
    '#f9f9f0',
]

colors = [ pygame.Color(i) for i in colors ]

TILESIZE = 48
TIMESTEP = 30.0

REGOLITH = 1
EXCAVATED = 2
STOCKPILE = 3


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
        path = [Point2(*c)]
        while parent.get(c, None) is not None:
            c = parent[c]
            path.append(Point2(*c))
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


class ExcavateAI(AIContext):
    def update(self, tile):
        x, y = map(int, self.sprite.position)[:2]

        if self.sprite.level.data[y][x] == REGOLITH:
            self.sprite.level.data[y][x] = EXCAVATED
            self.sprite.carried += 1
            self.done()


class SearchAndTravelAI(AIContext):
    def update(self, time):
        spr = self.sprite

        if not self.path:
            dest, dist = spr.level.nearest_tile(spr.position, self.tile_type)

            if dest:
                self.path = aStar(tuple(map(round, spr.position)), tuple(dest), (20, 20))
            else:
                self.done()
                return

        n = spr.position - self.path[-1] - (.5, .5)
        if abs(n) < .05:
            self.path.pop()
            if len(self.path) == 0:
                spr.move_vector = Vector2(0,0)
                self.done()
                return

        spr.move_vector = n.normalize()
        spr.position -= spr.move_vector * spr.travel_speed

    def enter(self):
        self.path = None

    def exit(self):
        self.path = None


class DropCarriedAI(AIContext):
    def update(self, tile):
        if self.sprite.carried > 0:
            x, y = map(int, self.sprite.position)[:2]

            if self.sprite.level.data[y][x] == STOCKPILE:
                self.sprite.carried -= 1
            else:
                self.done()
        else:
            self.done()



class GameObject(pygame.sprite.Sprite):
    def __init__(self, level):
        super(GameObject, self).__init__()
        self.travel_speed = 3/TIMESTEP
        self.level = level
        self.ai_stack = context.ContextDriver()
        self.ai_lists = []
        self.ai_cursor = 0 
        self.move_vector = Vector2(0,0)
        self.position = Vector2(0,0)
        self.init()

        self.pixel_size = self.world_size * TILESIZE

    def update(self, time):
        task = self.ai_stack.current_context
        if task:
            task.update(time)
        else:
            for task in reversed(self.ai_lists[0]):
                self.ai_stack.append(task)

class Harvester(GameObject):
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[-1])
        self.world_size = Vector2(.1, .5)
        self.carried = 0

        self.ai_lists.append([
            SearchAndTravelAI(sprite=self, tile_type=REGOLITH),
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

    font = pygame.font.Font(pygame.font.get_default_font(), 12)

    level = LevelMap((20, 20))

    level.data[6][6] = STOCKPILE

    tilemap = tilemap.TilemapRenderer([level], TILESIZE)

    h00 = Harvester(level)
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

        for i, c in enumerate(colors):
            screen.fill(c, (i*32+10,10,32,32))
            screen.blit(font.render(str(i+1), 1, (255,255,255)), (i*32+20, 44))

        pygame.display.flip()

        try:
            event = pygame.event.poll()
            #event = pygame.event.wait()
            if (event.type == QUIT) or (event.type == KEYDOWN): run = False
            if event.type == MOUSEMOTION:
                mx, my = event.pos

                x, y, z = game_group.tilemap.unproject_point(Vector3(mx, my, 0))
                try:
                    level.data[int(y)][int(x)] = EXCAVATED
                except IndexError:
                    pass

        except KeyboardInterrupt:
            run = False

