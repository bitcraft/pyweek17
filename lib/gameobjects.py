import pygame
import random
import context
from tasks import *
from const import *
from lib.euclid import Vector2, Point2, Point3, Vector3, Matrix4



pygame.mixer.init()

def load_sound(fn):
    sound = pygame.mixer.Sound(os.path.join('sounds', fn))
    sound.set_volume(volume)
    return sound


class GameObject(pygame.sprite.Sprite):
    def __init__(self, group, **kwarg):
        super(GameObject, self).__init__()
        self.ai_stack = context.ContextDriver()
        self.ai_lists = []
        self.travel_speed = 2/TIMESTEP
        self.move_vector = Vector3(0,0,0)
        self.position = Point3(0,0,0)
        self.power = 1
        self.max_hp = 10.0
        self.hp = 10
        self.xp = 0
        self.stuck = False
        self.carried = []

        self.__dict__.update(kwarg)

        self.init()

        group.add(self)
        self.level = group.level

    def update(self, time):
        if self.position.z > 0:
            self.position.z -= time/50.0
            return

        if self.position.z < 0:
            self.position.z = 0

        if self.stuck:
            return

        this_task = self.ai_stack.current_context
        if this_task is None:
            self.idle = True
            self.ai_stack = context.ContextDriver()
            for task in reversed(self.ai_lists[0]):
                self.ai_stack.append(task, start=False)
            self.ai_stack.current_context.__enter__()
        else:
            self.idle = False
            this_task.update(time)

    def kill(self):
        task = self.ai_stack.current_context
        if task:
            self.ai_stack.current_context.fail()
        super(GameObject, self).kill()


class Turret(GameObject):
    world_size = Vector2(.6, 1.4)

    def init(self):
        w, h = self.world_size * TILESIZE
        self.image = pygame.Surface((w, h))
        pygame.draw.rect(self.image, colors[88], (0,0,w/2,h))
        pygame.draw.rect(self.image, colors[91], (w/2,0,w/2,h))

        self.ai_lists.append([
            ShootEnemiesTask(sprite=self, target=[Hunter, Thief]),
        ])


class Minion(GameObject):
    death_sound = load_sound('miniondeath.wav')
    world_size = Vector2(.25, .5)

    def init(self):
        self._xp = 0
        self.idle = True

        self.ai_lists.append([
            RestTask(sprite=self),
            CollectTask(sprite=self, key=self.__class__),
            DepositTask(sprite=self, key=self.__class__)
        ])

        self.create_image()

    def create_image(self):
        sx, sy = self.world_size * TILESIZE * self.hp/self.max_hp
        if sx < 5: sx = 5
        if sy < 5: sy = 5
        self.image = pygame.Surface((sx, sy))
        self.image.fill(colors[3])
        for i in range(self.power):
            pygame.draw.line(self.image, (24,33,20), (2, i*3+2), (sx-3, i*3+2), 2)

    @property
    def xp(self):
        return self._xp

    @xp.setter
    def xp(self, xp):
        self._xp = xp
        self.hp += 1
        if xp >= 8:
            if self.power < 4:
                self.travel_speed *= 1.6
                self.power += 1
                self._xp = 0
                self.max_hp += 2
                self.hp += 2

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp):
        self._hp = hp

        if hp > self.max_hp:
            self._hp = self.max_hp

        elif hp <= 0:
            self._hp = 0
            self.death_sound.play()
            self.kill()
            return 

        self.create_image()

class Thief(GameObject):
    sounds = [ load_sound(i) for i in ('laser0.wav', 'laser1.wav', 'laser2.wav', 'laser3.wav') ]

    mine_sound = load_sound('thiefdig.wav')
    mine_sound.set_volume(.3)
    world_size = Vector2(.5, 1)

    def init(self):
        self.travel_speed = 1.5/TIMESTEP
        self.image = pygame.Surface((24, 48))
        self.image.fill(colors[ENERGY*16])
        self._hp = 30.0
        self.max_hp = 30.0
        self.power = 10
    
        self.ai_lists.append([
            SearchAndTravelTask(sprite=self, tile_type=[ENERGY], key=self.__class__),
            MineTask(sprite=self, duration=80.0, mine=4, target=ENERGY, callback=self.on_mine),
        ])

    def on_mine(self):
        self.mine_sound.stop()
        self.mine_sound.play()

    def update(self, time):
        self.hp += len(self.carried) / 2
        self.carried = []
        super(Thief, self).update(time)

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp):
        if self.position.z > 0:
            return 

        self._hp = hp
        if hp <= 0:
            self.kill()
            return
        if hp > 60:
            self._hp = 60

        sx, sy = self.world_size * TILESIZE * self.hp/self.max_hp
        if sx < 5: sx = 5
        if sy < 5: sy = 5
        self.image = pygame.Surface((sx, sy))
        self.image.fill(colors[ENERGY*16+8])


class Hunter(GameObject):
    world_size = Vector2(.5, 1)

    def init(self):
        self.travel_speed = 1.2/TIMESTEP
        self.image = pygame.Surface((24, 48))
        self.image.fill(colors[128])
        self.world_size = Vector2(.6, 1.2)
        self.max_hp = 30
        self.hp = self.max_hp

        self.ai_lists.append([
            HuntTask(sprite=self, target=[Minion]),
            ChompMinion(sprite=self),
        ])

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp):
        if self.position.z > 0:
            return 

        self._hp = hp
        if hp <= 0:
            self.kill()
            return
       
        sx, sy = self.world_size * TILESIZE * self.hp/self.max_hp
        if sx < 5: sx = 5
        if sy < 5: sy = 5
        self.image = pygame.Surface((sx, sy))
        self.image.fill(colors[128])

class Shuttle(GameObject):
    world_size = Vector2(.2, .5)

    def init(self):
        self.image = pygame.Surface((12, 24))
        self.image.fill(colors[-1])
        self.ai_lists.append([ShuttleFlyTask(sprite=self)])

