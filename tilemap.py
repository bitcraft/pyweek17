"""
rewrite of the tilmap engine for lib2d.
"""

from euclid import Vector2, Vector3, Point3, Matrix4
from itertools import product, chain, ifilter
import pygame, math


# this image will be used when a tile cannot be loaded
def generateDefaultImage(size):
    i = pygame.Surface(size)
    i.fill((0, 0, 0))
    i.set_alpha(128)
    return i


class TilemapRenderer:
    time_update = True

    def __init__(self, layers, tile_size):
        self.layers = layers
        self.tile_size = float(tile_size)
        self.visibleTileLayers = layers

        self.screen_offset = Vector3(600, 400, 0)
        self.world_offset = Vector3(10,10,0)

        ds = len(layers[0].data)
        self.view = pygame.Rect(0,0,ds,ds)

        self.reproject(math.radians(45))

        self.changed = True 
        self.queue = None
        self.dirty = []

    def center(self, (x, y)):
        pass

    def update(self, time=None):
        pass

    def reproject(self, rot):
        self.prj = Matrix4()
        self.prj.scale(self.tile_size, self.tile_size, 1.0)
        self.prj.rotate_axis(math.radians(60), Vector3(1,0,0))
        self.prj.rotate_axis(rot, Vector3(0,0,1))

        self.inv_prj = Matrix4()
        self.inv_prj.scale(self.tile_size, self.tile_size / 2, 1.0)
        self.inv_prj.rotate_axis(rot, Vector3(0,0,1))
        self.inv_prj = self.inv_prj.inverse()

    def draw(self, surface, rect, sprites=[]):
        """
        draw the map onto a surface.
        """

        place = self.place
        surblit = surface.blit

        for rect, dirty in self.dirty:
            surblit(dirty, rect)
        self.dirty = []

        if self.changed:
            self.redraw(surface)
            self.changed = False

        if self.queue:
            self.flushQueue(surface)

        for spr in sprites:
            p = self.project_point(spr.position)
            w, h = spr.image.get_size()
            p.y -= h
            p.x -= w / 2
            rect = int(p.x), int(p.y), w, h
            dirty = pygame.Surface((w, h))
            dirty.blit(surface, (0,0), area=rect)
            self.dirty.append((pygame.Rect(rect), dirty))
            surblit(spr.image, rect)

    def place(self, sprite):
        """ adjust the apparent position of a sprite """
        p = self.project_point(sprite.position)
        w, h = sprite.image.get_size()
        p.y -= h
        p.x -= w / 2
        return map(int, p[:2])

    def paintTile(self, surface, (x, y, l)):
        try:
            value = self.layers[l].data[y][x]  
        except IndexError:
            return

        if not value:
            return

        ax, ay, az = self.project_point(Vector3(x, y, 0))
        bx, by, bz = self.project_point(Vector3(x+1, y, 0))
        cx, cy, cz = self.project_point(Vector3(x+1, y+1, 0))
        dx, dy, dz = self.project_point(Vector3(x, y+1, 0))

        points = ((ax, ay), (bx, by), (cx, cy), (dx, dy))

        pygame.draw.polygon(surface, self.layers[l].colors[value-1], points)

    def project_point(self, point):
        """ world --> screen """
        return self.prj * (point - self.world_offset) + self.screen_offset

    def unproject_point(self, point):
        """ screen --> world """
        return self.inv_prj * (point - self.screen_offset) + self.world_offset

    def flushQueue(self, surface):
        surface.lock()
        [ self.paintTile(surface, i) for i in self.queue ]
        surface.unlock()
        self.queue = None

    def redraw(self, surface):
        self.queue = product(xrange(self.view.left, self.view.right),
                             xrange(self.view.top, self.view.bottom),
                             xrange(len(self.visibleTileLayers)))
        self.flushQueue(surface)
