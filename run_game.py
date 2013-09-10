from itertools import product, cycle
import pygame
import random
import math
import os
import fnmatch
import re

from pygame.locals import *

from lib.euclid import Point3
from lib.levelmap import LevelMap
from lib.tilemap import TilemapRenderer
from lib.const import *
from lib.gameobjects import *
from lib import Scheduler

screen_dim = (1200, 800)


pygame.init()
pygame.font.init()
pygame.mixer.init()

class Bonus:
    pass

class StatusManager:
    def __init__(self, color=(255,255,255), life=3000):
        self.font = pygame.font.Font(pygame.font.get_default_font(), 16)
        self.life = life
        self.color = color
        self._msg_cache = {}
        self.messages = set()
        self.times = {}

    def add(self, msg):
        self.messages.add(msg)
        self.times[msg] = pygame.time.get_ticks()

    def draw(self, surface, (x, y)):
        to_remove = []
        for i, msg in enumerate(self.messages):
            if pygame.time.get_ticks() - self.times[msg] > self.life:
                to_remove.append(msg)
                continue

            try:
                surface= self._msg_cache[msg]
            except KeyError:
                surface = font.render(status_msg[msg], 1, self.color)
                self._msg_cache[msg] = surface

            screen.blit(surface, (x-surface.get_size()[0]-30, y+i*16))
            
        [ self.messages.remove(i) for i in to_remove ]

status_mgr = StatusManager()
hint_mgr = StatusManager((200,224,240), 10000)

class GameGroup(pygame.sprite.Group):
    def __init__(self, level):
        pygame.sprite.Group.__init__(self)
        self.classdict = collections.defaultdict(list)
        self.level = level
        self.tilemap = TilemapRenderer(level, TILESIZE)

        font = pygame.font.Font(pygame.font.get_default_font(), 16)
        self.idle_stamp = font.render("?", 1, colors[60])

    def update(self, time):
        self.tilemap.update(time)
        super(GameGroup, self).update(time)

    def set_player(self, player):
        self.player = player

    def draw(self, surface, area):
        sprites = self.sprites()

        self.tilemap.draw(surface, area, sprites)

        for s in sprites:
            try:
                p = getattr(s.ai_stack.current_context, "progress", -1)
            except AttributeError:
                continue

            point = None
            if p>-1:
                h = s.image.get_size()[1]
                point = self.tilemap.project_point(s.position)
                small_progress(surface, colors[0], colors[-1], (point[0]-14, point[1]-h-5), p)

            if isinstance(s, Minion):
                if s.idle:
                    status_mgr.add('idle')

                    if point is None:
                        point = self.tilemap.project_point(s.position)
                        h = s.image.get_size()[1]
                    surface.blit(self.idle_stamp, (point[0]-5, point[1]-h-20))


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

class Player:
    energy = 0
    max_energy = 1
    regolith = 0
    max_regolith = 50.0
    food = 2
    max_food = 10
    tilechange = 1
    tile_stack = []
    status = 'idle'

player = Player()

def draw_bar(s, c1, c2, r, v):
    if v>1:v=1
    s.fill(c1, r)
    s.fill(c2, (r.topleft, (math.ceil(r.width*v), r.height)))

def small_progress(s, c1, c2, point, v):
    x = math.ceil(28.0*v)
    if x > 28: x = 28
    s.fill(c2, (point, (30, 8)))
    s.fill(c1, (point[0]+1, point[1]+1, x, 6))

def load_sound(fn):
    sound = pygame.mixer.Sound(os.path.join('sounds', fn))
    sound.set_volume(volume)
    return sound

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


def glob(which, where='.'):
    rule = re.compile(fnmatch.translate(which), re.IGNORECASE)
    return [os.path.join(where, name) for name in os.listdir(where) if rule.match(name)]

def random_pos(minimum=-2, maximum=2):
    p = Vector3(random.randint(minimum,maximum), random.randint(minimum,maximum), 0)
    return p * 20

if __name__ == '__main__':
    allhints = cycle("clone1 clone2 regolith1 regolith2".split())

    pygame.mixer.set_num_channels(32)

    music = glob('*mp3', 'music')
    pygame.mixer.music.set_volume(.6)
    pygame.mixer.music.load(music[0])
    pygame.mixer.music.play(-1)

    screen = pygame.display.set_mode(screen_dim)

    font = pygame.font.Font(pygame.font.get_default_font(), 14)
    bigfont = pygame.font.Font(pygame.font.get_default_font(), 24)

    level = LevelMap((20, 20), BARREN)

    game_group = GameGroup(level)
    game_group.set_player(player)

    for p in ((5,5,0), (5,15,0), (15,15,0), (15,5,0)):
        t = Turret(game_group)
        t.position = Vector3(*p)
        m = Minion(game_group)
        m.position = Vector3(*p) + (1.5,1.5,0)

    area = pygame.Rect((0,0), screen_dim)

    old_hl = []
    paint_counter = 100
    tblock_shape = [ Vector3(*p) for p in tblocks[0] ]
    tblock_height = 7
    tblock_type = STOCKPILE
    tblock_deny_rotate = False
    wave_number = 0

    def wave():
        global wave_number

        status_mgr.add('prepare')

        wave_number += 1
        for i in xrange(wave_number):
            e = Thief(game_group)
            e.position = random_pos()

        for i in xrange(wave_number):
            e = Hunter(game_group)
            e.position = random_pos()

    wave()

    def hint():
        hint_mgr.add(next(allhints))

    def lower_tblock(v=-1):
        global tblock_height, tblock_deny_rotate, tblock_shape, tblock_position, tblock_type

        tblock_height += v

        if tblock_height <= 0:
            hl = tuple([ map(int,p + tblock_position) for p in tblock_shape ])
            for x, y, l in hl:
                try:
                    tile, value = level.get_tile((x, y))
                    if tile == BARREN:
                        level.set_tile((x, y), tblock_type)
                    else:
                        level.set_tile((x, y), BARREN)
                except (TypeError, IndexError):
                    pass

            index = random.randint(0, len(tblocks)-1)
            tblock_type = random.randint(2, 5)
            tblock_height = 7
            tblock_deny_rotate = bool(index == 0)
            tblock_shape = [ Vector3(*p) for p in tblocks[index] ]

            block = level.scan_block()
            if block is not None:
                x, y = block
                for x, y in product(xrange(x, x+5), xrange(y, y+5)):
                    level.set_tile((x, y), REGOLITH)

    clock = pygame.time.Clock()
    scheduler = Scheduler()
    scheduler.schedule_interval(1000, lower_tblock)
    scheduler.schedule_interval(20000, wave)
    scheduler.schedule_interval(12000, hint)

    mx, my = pygame.mouse.get_pos()
    tblock_position = game_group.tilemap.unproject_point(Vector3(mx, my, tblock_height))

    last_low_energy = pygame.time.get_ticks()

    hint()

    run = True
    while run:
        td = clock.tick(60)
        game_group.update(60.0/td)

        event = pygame.event.poll()
        scheduler.test(event)
        if event.type == QUIT: run = False
        elif event.type == MOUSEMOTION:
            mx, my = event.pos
            tblock_position = game_group.tilemap.unproject_point(Vector3(mx, my, tblock_height))
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                lower_tblock(-100)
            elif event.button == 3:
                tblock_shape = [ rotate(p, 90) for p in tblock_shape ]
        elif event.type == KEYDOWN:
            if event.key == K_LEFT:
                if not tblock_deny_rotate:
                    tblock_shape = [ rotate(p, 90) for p in tblock_shape ]
            elif event.key == K_RIGHT:
                if not tblock_deny_rotate:
                    tblock_shape = [ rotate(p, -90) for p in tblock_shape ]
            elif event.key == K_DOWN:
                lower_tblock()

        player.max_energy = float(level.get_total(ENERGY) + 1)
        player.energy += player.max_energy*td/1000
        if player.energy > player.max_energy:
            player.energy = player.max_energy

        if player.energy < player.max_energy /2:
            if pygame.time.get_ticks() - last_low_energy > 1000:
                last_low_energy = pygame.time.get_ticks()
                status_mgr.add('lowenergy')
        elif player.energy > player.max_energy * 1.8:
            last_low_energy = pygame.time.get_ticks()


        paint_counter += 1
        if paint_counter >= 2:
            paint_counter = 0

            game_group.draw(screen, area)

            tblock_position.z = tblock_height
            hl = tuple([ map(int,p + tblock_position) for p in tblock_shape ])
            for block in old_hl:
                game_group.tilemap.unhighlight(block)
            for block in hl:
                game_group.tilemap.highlight(block)
                game_group.tilemap.paintTile(screen, block, color=colors[tblock_type*16], outline=True)
            old_hl = hl

            x = 10
            y = 10
            total = float(level.width * level.height)

            draw_bar(screen, (255,255,255), colors[ENERGY*16], Rect(x+100, y, 10+player.max_energy*4, 16), player.energy/player.max_energy)
            msg = "{0:.2f} / {1:.2f}".format(player.energy, player.max_energy)

            screen.blit(font.render("wave: ", 1, colors[STOCKPILE*16]), (x, y+30))
            screen.blit(bigfont.render(str(wave_number), 1, (200,200,240)), (x+50, y+23))

            screen.blit(font.render(msg, 1, colors[ENERGY*16]), (x, y))

            status_mgr.draw(screen, (1200, 10))
            hint_mgr.draw(screen, (1200, 60))

            pygame.display.flip()
