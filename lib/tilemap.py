from euclid import Vector2, Vector3, Point3, Matrix4
from itertools import product 
import pygame, math
from const import colors



class TilemapRenderer(object):
    def __init__(self, layer, tile_size):
        self.layer = layer
        self.tile_size = float(tile_size)
        layer.set_renderer(self)

        self.screen_offset = Vector3(600, 400, 0)
        self.world_offset = Vector3(10,10,0)

        ds = len(layer.data)
        self.view = pygame.Rect(0,0,ds,ds)

        self.reproject(math.radians(45))

        self.surface = None
        self.highlighted = set()
        self.refresh = 1
        self.queue = set()
        self.dirty_rect_list = []
        
        self.surface = pygame.Surface((1200, 800))

    def center(self, (x, y)):
        pass

    def update(self, time=None):
        #self.prj.rotate_axis(0.01, Vector3(0,0,1))
        #self.changed = 1
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

    def highlight(self, (x, y, z)):
        position = ((int(x), int(y)))
        if position not in self.highlighted:
            self.refresh = True
            self.highlighted.add(position) 

    def unhighlight(self, (x, y, z)):
        try:
            self.highlighted.remove(((int(x), int(y))))
        except KeyError:
            pass

    def draw(self, surface, rect, sprites=[]):
        """
        draw the map onto a surface.
        """

        place = self.place
        surblit = surface.blit

        if len(self.queue) == 0:
            self.flushQueue()
            self.refresh = 1

        if self.refresh:
            self.refresh = 0
            self.redraw()
            surface.blit(self.surface, (0,0))
            self.dirty_rect_list = []

        for rect in self.dirty_rect_list:
            surblit(self.surface, rect, area=rect)

        self.dirty_rect_list = []

        sprites = [ (sum(s.position), s) for s in sprites ]
        sprites.sort()

        for index, spr in sprites:
            p = self.project_point(spr.position)
            try:
                w, h = spr.image.get_size()
                p.y -= h
                p.x -= w / 2
                rect = pygame.Rect(int(p.x), int(p.y), w, h)
                self.dirty_rect_list.append(rect)
                surblit(spr.image, rect)
            except AttributeError:
                p2 = self.project_point(spr.endpoint)
                pygame.draw.line(surface, (192, 200, 255), (p.x, p.y), (p2.x, p2.y), int(spr.life))
                rect = pygame.Rect(p.x, p.y, p.x - p2.x, p.y - p2.y)
                self.dirty_rect_list.append(rect)

    def place(self, sprite):
        """ adjust the apparent position of a sprite """
        p = self.project_point(sprite.position)
        w, h = sprite.image.get_size()
        p.y -= h
        p.x -= w / 2
        return map(int, p[:2])

    def mark_changed(self, position):
        self.queue.add((position[0], position[1], 0))

    def paintTile(self, surface, (x, y, z), width=0, color=None, outline=False):
        ax, ay, az = self.project_point(Vector3(x, y, z))
        bx, by, bz = self.project_point(Vector3(x+1, y, z))
        cx, cy, cz = self.project_point(Vector3(x+1, y+1, z))
        dx, dy, dz = self.project_point(Vector3(x, y+1, z))

        points = ((ax, ay), (bx, by), (cx, cy), (dx, dy))

        if color is None:
            color = colors[self.layer.get_raw((x, y))]

        pygame.draw.polygon(surface, color, points, width)
        if outline:
            pygame.draw.lines(surface, (200,200,180), 1, points, 3)

    def project_point(self, point):
        """ world --> screen """
        return self.prj * (point - self.world_offset) + self.screen_offset

    def unproject_point(self, point):
        """ screen --> world """
        return self.inv_prj * (point - self.screen_offset) + self.world_offset

    def flushQueue(self):
        self.surface.lock()
        [ self.paintTile(self.surface, i) for i in self.queue ]
        self.surface.unlock()
        self.queue = set()

    def redraw(self):
        if self.surface:
            self.surface.fill((0,0,0))
        else:
            self.surface = pygame.Surface((1200, 800))
        self.queue = product(xrange(self.view.left, self.view.right),
                             xrange(self.view.top, self.view.bottom),
                             xrange(1))
        self.flushQueue()

        self.surface.lock()
        for x, y in self.highlighted:
            try:
                self.paintTile(self.surface, (x, y, 0), width=2, color=(255,255,240))
            except IndexError:
                pass
        self.surface.unlock()
