import pygame
import array
import random
import tilemap
import context
import math
from itertools import product
from euclid import Vector2, Vector3, Matrix4

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
        
        for position in self.tiles_of_type(tile_type):
            d = distance2(position, origin)
            if d < nearest[1]:
                nearest = position, d

        return Vector2(*nearest[0]), nearest[1] if nearest[0] else None


class AIContext(context.Context):
    def update(self, time):
        pass


class MoveRandomAI(AIContext):
    def update(self, time):
        self.sprite.position += self.sprite.move_vector * time
        if random.random() > .90:
            self.sprite.move_vector = Vector2(
                random.uniform(-.05/TIMESTEP, .05/TIMESTEP),
                random.uniform(-.05/TIMESTEP, .05/TIMESTEP))


class MoveToMaterialsAI(AIContext):
    def update(self, time):
        origin = Vector2(*self.sprite.rect.center)
        origin /= TILESIZE
        dest, dist = self.sprite.level.nearest_tile(origin, MATERIALS)

        norm = abs(dest - origin)

        if norm:
            delta = dest / norm
            self.sprite.rect.x += delta.x / dist * time
            self.sprite.rect.y += delta.y / dist * time

class GameObject(pygame.sprite.Sprite):
    def __init__(self, level):
        super(GameObject, self).__init__()
        self.level = level
        self.ai_stack = context.ContextDriver()
        self.move_vector = Vector2(.05/TIMESTEP,0)
        self.position = Vector2(0,0)
        self.init()

        self.pixel_size = self.world_size * TILESIZE

    def update(self, time):
        try:
            self.ai_stack.current_context.update(time)
        except:
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

    h00.ai_stack.append(MoveRandomAI(sprite=h00))
    #h00.ai_stack.append(MoveToMaterialsAI(sprite=h00))
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

