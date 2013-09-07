from itertools import product
import pygame
import random
import math
import os

from pygame.locals import *

from lib.euclid import Point3
from lib.pathfinding import aStar
from lib.levelmap import LevelMap
from lib.tilemap import TilemapRenderer
from lib.const import *
from lib.gameobjects import *


screen_dim = (1200, 800)


class IsoGroup(pygame.sprite.Group):
    def __init__(self):
        pygame.sprite.Group.__init__(self)
        self.classdict = collections.defaultdict(list)

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
            p = getattr(s.ai_stack.current_context, "progress", -1)
            if p>-1:
                point = self.tilemap.project_point(s.position + (-.4,0,.8))
                point = map(int, point[:2])
                small_progress(surface, colors[0], colors[-1], point, p)

    def add_internal(self, sprite):
        self.spritedict[sprite] = 0
        self.classdict[sprite.__class__].append(sprite)

    def remove_internal(self, sprite):
        r = self.spritedict[sprite]
        if r:
            self.lostsprites.append(r)
        del self.spritedict[sprite]
        self.classdict[sprite.__class__].remove(sprite)

    def of_class(self, l):
        for s in self.sprites():
            if s.__class__ in l:
                yield s

class Scheduler:
    def __init__(self):
        self.callbacks = {}
        self.next_event = pygame.USEREVENT

    def test(self, event):
        try:
            self.callbacks[event.type]()
        except KeyError:
            pass

    def schedule_interval(self, interval, callback):
        event = self.next_event
        self.callbacks[event] = callback
        pygame.time.set_timer(event, interval)
        pygame.event.set_allowed([event])
        self.next_event += 1
        return event

class Player:
    energy = 0
    max_energy = 50.0
    regolith = 0
    max_regolith = 50.0
    food = 2
    max_food = 10
    tilechange = 1
    tile_stack = []

player = Player()


def draw_bar(s, c1, c2, r, v):
    s.fill(c1, r)
    s.fill(c2, (r.topleft, (r.w, r.h-r.h*v)))

def small_progress(s, c1, c2, point, v):
    x = math.ceil(28.0*v)
    if x > 28: x = 28
    s.fill(c2, (point, (30, 8)))
    s.fill(c1, (point[0]+1, point[1]+1, x, 6))

def load_sound(fn):
    return pygame.mixer.Sound(os.path.join('sounds', fn))

tblocks = [
    ((0,0,0), (1,0,0), (1,-1,0), (0,-1,0)),
    ((0,0,0), (1,0,0), (-1,0,0), (0,1,0)),
    ((-2,0,0), (-1,0,0), (0,0,0), (1,0,0), (2,0,0)),
    ((-1,-1,0), (0,-1,0), (0,0,0), (1,0,0)),
    ((-1,0,0), (0,0,0), (0,-1,0), (1,-1,0))
]

if __name__ == '__main__':
    from itertools import product


    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode(screen_dim)

    beep = load_sound('beep.wav')

    font = pygame.font.Font(pygame.font.get_default_font(), 12)

    level_w, level_h = 20, 20
    level = LevelMap((level_w, level_h))

    for (y, x) in product(xrange(level_h), xrange(level_w)):
        level.set_tile((x, y), REGOLITH)

    for x in xrange(level_w):
        level.set_tile((x, -1), WATER)

    level_w += 1
    level_h += 1

    level.set_tile((4,4), STOCKPILE)
    level.set_tile((4,16), FARM)
    level.set_tile((16,4), FARM)
    level.set_tile((16,4), KITCHEN)
    level.set_tile((10,10), ORIGIN)

    tilemap = TilemapRenderer(level, TILESIZE)

    game_group = IsoGroup()
    game_group.set_tilemap(tilemap, TILESIZE)

    h = Harvester(level)
    h.position = Vector3(10, 10, 0)
    game_group.add(h)

    for i in xrange(1):
        e = Hunter(level)
        e.position = Vector3(random.uniform(0,20), random.uniform(0,20), 0)
        game_group.add(e)

    t = Turret(level)
    t.position = Vector3(11, 8, 0)
    game_group.add(t)

    for i in xrange(3):
        m = Minion(level)
        m.position = Vector3(random.uniform(0,20), random.uniform(0,20), 0)
        game_group.add(m)

    area = pygame.Rect((0,0), screen_dim)

    old_hl = []
    paint_counter = 100
    current_tblock = [ Vector3(*p) for p in tblocks[0] ]
    tblock_height = 7
    tblock_type = STOCKPILE
    tblock_deny_rotate = False

    def wave():
        for i in xrange(3):
            e = Thief(level)
            e.position = Vector3(random.uniform(0,20), random.uniform(0,20), 0)
            game_group.add(e)


    def scan_block():
        cache = {} 
        
        def scan_row(x, y):
            try:
                return cache[(x, y)]
            except KeyError:
                for i in xrange(x, x+5):
                    tile, value = level.get_tile((i, y))
                    if tile == REGOLITH:
                        cache[(x, y)] = False
                        return False
                cache[(x, y)] = True
                return True

        for y, x in product(xrange(level_h-5), xrange(level_w-5)):
            for i in xrange(y, y+5):
                found = scan_row(x, i)
                if not found: 
                    break

            if found:
                return x, y

        return None

    def lower_tblock(v=-1):
        global tblock_height, tblock_deny_rotate, current_tblock, tblock_position

        tblock_height += v

        if tblock_height <= 0:
            tblock_height = 7
            hl = tuple([ map(int,p + tblock_position) for p in current_tblock ])
            for x, y, l in hl:
                try:
                    level.set_tile((x, y), tblock_type)
                except (TypeError, IndexError):
                    pass

            index = random.randint(0, len(tblocks)-1)
            tblock_deny_rotate = bool(index == 0)
            current_tblock = [ Vector3(*p) for p in tblocks[index] ]

            block = scan_block()
            if block is not None:
                x, y = block
                for x, y in product(xrange(x, x+5), xrange(y, y+5)):
                    level.set_tile((x, y), REGOLITH)


    def rotate(v, t):
        if v.x == v.y == 0:
            return v
        r = math.radians(t)
        cos = math.cos(r)
        sin = math.sin(r)
        x = v.x*cos - v.y*sin
        y = v.x*sin + v.y*cos
        v.x = x
        v.y = y
        return v

    clock = pygame.time.Clock()
    scheduler = Scheduler()
    scheduler.schedule_interval(1000, lower_tblock)
    scheduler.schedule_interval(100000, wave)

    mx, my = pygame.mouse.get_pos()
    tblock_position = game_group.tilemap.unproject_point(Vector3(mx, my, tblock_height))

    run = True
    while run:

        try:
            event = pygame.event.poll()
            scheduler.test(event)
            if event.type == QUIT: run = False
            elif event.type == MOUSEMOTION:
                mx, my = event.pos
                tblock_position = game_group.tilemap.unproject_point(Vector3(mx, my, tblock_height))
            elif event.type == MOUSEBUTTONDOWN:
                print event.button
                if event.button == 1:
                    lower_tblock(-100)
                elif event.button == 3:
                    current_tblock = [ rotate(p, 90) for p in current_tblock ]
            elif event.type == KEYDOWN:
                if event.key == K_LEFT:
                    if not tblock_deny_rotate:
                        current_tblock = [ rotate(p, 90) for p in current_tblock ]
                elif event.key == K_RIGHT:
                    if not tblock_deny_rotate:
                        current_tblock = [ rotate(p, -90) for p in current_tblock ]
                elif event.key == K_DOWN:
                    lower_tblock()

        except:
            raise

        paint_counter += 1
        if paint_counter >= 2:
            game_group.draw(screen, area)
            draw_bar(screen, colors[REGOLITH], colors[64], Rect(10, 60, 32, 128), player.energy / player.max_energy)
            draw_bar(screen, colors[REGOLITH], colors[64], Rect(48, 60, 32, 128), player.regolith / player.max_regolith)
            draw_bar(screen, colors[FARM], colors[64], Rect(10, 200, 32, 128), player.food / player.max_food)
            tblock_position.z = tblock_height
            hl = tuple([ map(int,p + tblock_position) for p in current_tblock ])
            for block in old_hl:
                game_group.tilemap.unhighlight(block)
            for block in hl:
                game_group.tilemap.highlight(block)
                game_group.tilemap.paintTile(screen, block, color=(64,64,64))
            old_hl = hl

        if paint_counter >= 2:
            paint_counter = 0
            pygame.display.flip()

        td = clock.tick(60)
        game_group.update(60.0/td)
