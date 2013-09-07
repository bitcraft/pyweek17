import pygame
import random
import context
from tasks import *
from const import *
from lib.euclid import Vector2, Point2, Point3, Vector3, Matrix4



class GameObject(pygame.sprite.Sprite):
    def __init__(self, level, **kwarg):
        super(GameObject, self).__init__()
        self.travel_speed = 2/TIMESTEP
        self.level = level
        self.ai_stack = context.ContextDriver()
        self.ai_lists = []
        self.ai_cursor = 0 
        self.move_vector = Vector3(0,0,0)
        self.position = Vector3(0,0,0)
        self._hp = 10
        self.max_hp = 10.0
        self.stuck = False

        self.__dict__.update(kwarg)

        self.init()

        self.pixel_size = self.world_size * TILESIZE

    def update(self, time):
        if self.stuck:
            return

        this_task = self.ai_stack.current_context
        if this_task is None:
            self.ai_stack = context.ContextDriver()
            for task in reversed(self.ai_lists[0]):
                self.ai_stack.append(task, start=False)
            self.ai_stack.current_context.__enter__()
        else:
            this_task.update(time)

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp):
        self._hp = hp

class Harvester(GameObject):
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill((random.randint(64, 255), random.randint(64, 255), random.randint(64, 255)))
        self.world_size = Vector2(.1, .5)
        self.carried = 0

        self.ai_lists.append([
            SearchAndTravelTask(sprite=self, tile_type=[REGOLITH], key=REGOLITH),
            ExcavateTask(sprite=self),
            SearchAndTravelTask(sprite=self, tile_type=[STOCKPILE,ORIGIN]),
            DropCarriedTask(sprite=self)
        ])

class Missile(GameObject):
    def init(self):
        self.image = pygame.Surface((4, 4))
        self.image.fill((255,255,255))
        self.world_size = Vector2(.1, .1)
        self.travel_speed = 15/TIMESTEP

        self.ai_lists.append([
            MissileMoveTask(sprite=self, target=self.target)
        ])

class Turret(GameObject):
    def init(self):
        self.image = pygame.Surface((24, 24))
        self.image.fill(colors[48])
        self.world_size = Vector2(.2, .5)

        self.ai_lists.append([
            ShootEnemiesTask(sprite=self, target=[Hunter, Thief]),
        ])

class Minion(GameObject):
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[3])
        self.world_size = Vector2(.2, .5)
        self.carried = 0

        self.ai_lists.append([
            SearchAndTravelTask(sprite=self, tile_type=[FARM]),
            FarmTask(sprite=self),
            SearchAndTravelTask(sprite=self, tile_type=[KITCHEN]),
            DropCarriedTask(sprite=self)
        ])

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp):
        self._hp = hp
        if hp <= 0:
            self._hp = 0
            self.kill()
            return
        
        sx = int(12 * (hp/self.max_hp))
        sy = int(24 * (hp/self.max_hp))
        if sx < 2: sx = 2
        if sy < 2: sy = 2
        self.image = pygame.Surface((sx, sy))
        self.image.fill(colors[3])

class Thief(GameObject):
    def init(self):
        self.travel_speed = .25/TIMESTEP
        self.image = pygame.Surface((24, 48))
        self.image.fill(colors[16])
        self.world_size = Vector2(.2, .5)
        self._hp = 100.0
        self.max_hp = 100.0

        self.ai_lists.append([
            SearchAndTravelTask(sprite=self, tile_type=[STOCKPILE]),
            StealStockpileTask(sprite=self),
        ])

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp):
        self._hp = hp
        if hp <= 0:
            self.kill()
            return

        sx = int(24 * (hp/self.max_hp))
        sy = int(48 * (hp/self.max_hp))
        if sx < 2: sx = 2
        if sy < 2: sy = 2
        self.image = pygame.Surface((sx, sy))
        self.image.fill(colors[16])

class Hunter(GameObject):
    def init(self):
        self.travel_speed = .5/TIMESTEP
        self.image = pygame.Surface((24, 48))
        self.image.fill(colors[128])
        self.world_size = Vector2(.2, .5)
        self._hp = 100.0
        self.max_hp = 100.0

        self.ai_lists.append([
            HuntTask(sprite=self, target=[Minion]),
            ChompMinion(sprite=self),
        ])

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp):
        self._hp = hp
        if hp <= 0:
            self.kill()
            return
        
        sx = int(24 * (hp/self.max_hp))
        sy = int(48 * (hp/self.max_hp))
        if sx < 2: sx = 2
        if sy < 2: sy = 2
        self.image = pygame.Surface((sx, sy))
        self.image.fill(colors[128])


class Shuttle(GameObject):
    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[-1])
        self.world_size = Vector2(.2, .5)
        self.ai_lists.append([ShuttleFlyTask(sprite=self)])

