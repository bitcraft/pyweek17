import collections
import random
import os

from euclid import Vector3, Line3, Point3
from const import *
import context

pygame.mixer.init()

def load_sound(fn):
    sound = pygame.mixer.Sound(os.path.join('sounds', fn))
    sound.set_volume(volume)
    return sound

class Laser(pygame.sprite.Sprite):
    def __init__(self, start, end):
        pygame.sprite.Sprite.__init__(self)
        self.position = start
        self.endpoint = end
        self.life = 12.0

    def update(self, time):
        self.life -= time
        if self.life <= 0:
            self.kill()

class Task(context.Context):
    def update(self, time):
        pass

class ShuttleFlyTask(Task):
    def enter(self):
        self.sprite.move_vector = Vector3(0,0,.02/TIMESTEP)

    def update(self, time):
        self.sprite.position += self.sprite.move_vector * time

    def exit(self):
        self.sprite.move_vector = Vector3(0,0,0)

class MoveRandomTask(Task):
    def update(self, time):
        self.sprite.position += self.sprite.move_vector * time
        if random.random() > .90:
            s = self.sprite.travel_speed
            self.sprite.move_vector = Vector3(random.uniform(-s, s), random.uniform(-s, s), 0)


class MineTask(Task):
    duration = 150.0
    mine = 1
    steps = 15
    empty = BARREN
    target = None

    def update(self, time):
        self._progress += time
        self.progress = self._progress / self.duration

        x, y, z = map(int, self.sprite.position)
        if not self._mining == self.sprite.level.get_tile((x, y)):
            self.release()
            self.done()

        elif self.progress >= 1.0:
            spr = self.sprite
            x, y, z = map(int, spr.position)
            t, v = spr.level.get_tile((x, y))
            v += self.mine
            if v > self.steps:
                spr.level.set_tile((x, y), self.empty)
            else:
                spr.level.set_tile((x, y), t, v)
            spr.carried.append(t)
            spr.xp += 1
            self.release()
            self.done()

    def enter(self):
        if len(self.sprite.carried) >= 1:
            self.release()
            self.fail()
        else:
            self._progress = 0.0
            self.progress = 0.0
            x, y, z = map(int, self.sprite.position)
            try:
                t, v = self.sprite.level.get_tile((x, y))
            except:
                self.release()
                self.fail()
                return

            if self.target is None or self.target == t:
                self._mining = (t, v)
            else:
                self.release()
                self.fail()

    def release(self):
        try:
            my_key, dest = getattr(self.parent, "tile_lock")
            ExclusiveKeys[my_key].remove(dest)
            if len(ExclusiveKeys[my_key]) == 0:
                del ExclusiveKeys[my_key]
        except (AttributeError, KeyError, ValueError):
            pass

class IntervalTask(Task):
    interval = 100.0
    show = True
    spread = 0
    offset = 0

    def test(self):
        return True

    def update(self, time):
        if self.test():
            self.timer += time
            if self.timer <= self.interval:
                if self.show: self.progress = self.timer/self.interval
            else:
                self.timer = 0.0
                self.work()
        elif self.show:
            self.progress = -1

    def work(self):
        pass

    def enter(self):
        self.timer = 0.0
        if self.spread:
            self.interval += random.uniform(-self.spread, self.spread)


class RestTask(IntervalTask):
    """ reduce stress on cpu by creating a small rest """
    interval = 100.0
    show = False

    def work(self):
        self.done()

class ChompMinion(IntervalTask):
    interval = 80.0
    show = False

    sound = load_sound('chomp.wav')
    sound.set_volume(.7)

    def work(self):
        spr = self.sprite
        victim = self.parent.victim

        self.sound.play()

        if victim is None:
            self.done()
            return

        victim.hp -= 2
        if victim.hp <= 0:
            self.done()

    def fail(self):
        if self.parent.victim:
            self.parent.victim.stuck = False
        super(ChompMinion, self).fail()


class ShootEnemiesTask(IntervalTask):
    interval = 40.0
    spread = 20
    energy_cost = 1
    radius = 10
    shots = 5

    sounds = [ load_sound("laser{}.wav".format(i)) for i in range(6) ]

    def test(self):
        group = self.sprite.groups()[0]
        self.cache = [ i for i in group.of_class(self.target) if abs(i.position - self.sprite.position) <= 7 ]
        return self.cache and group.player.energy >= self.energy_cost

    def work(self):
        spr = self.sprite
        group = spr.groups()[0]

        random.choice(self.sounds).play()

        for i in range(self.shots):
            if group.player.energy >= self.energy_cost:
                group.player.energy -= self.energy_cost
                e = random.choice(self.cache)
                z = e.world_size.y * e.hp/e.max_hp / 2
                self.sprite.groups()[0].add(Laser(spr.position + (0,0,1.4), e.position + (0,0,z)))
                e.hp -= 2
            else:
                break

ExclusiveKeys = collections.defaultdict(set)

class SearchAndTravelTask(Task):
    exclusive = True
    impassable = None
    timeout = 15000  # masks some underlying pathfinding bug

    def update(self, time):
        self.time += time
        if self.time >= self.timeout:
            return self.fail()

        spr = self.sprite
        x, y = self.path[-1]
        n = spr.position - (x, y, 0)
        if abs(n) < .1:
            self.path.pop()
            if len(self.path) == 0:
                if self.complete:
                    spr.move_vector = Vector3(0,0,0)
                    spr.xp += 1
                    return self.done()
                else:
                    return self.plan()

        spr.move_vector = n.normalize()
        spr.position -= spr.move_vector * spr.travel_speed

    @property
    def targets(self):
        return self.tile_type

    def plan(self):
        self.release()

        spr = self.sprite

        self.path, self.complete = spr.level.pathfind_type(spr.position, self.targets, ExclusiveKeys[self.my_key], self.impassable)

        if self.path == [] and self.complete:
            self.fail()
            return

        if self.exclusive:
            dest = tuple(map(int, self.path[0]))
            ExclusiveKeys[self.my_key].add(dest)
            self.parent.tile_lock = self.my_key, dest

    def enter(self):
        self.time = 0.0
        self.my_key = getattr(self, "key", self)
        self.plan()
   
    def fail(self):
        self.release()
        super(SearchAndTravelTask, self).fail()

    def release(self):
        try:
            my_key, dest = getattr(self.parent, "tile_lock")
            ExclusiveKeys[my_key].remove(dest)
            if len(ExclusiveKeys[my_key]) == 0:
                del ExclusiveKeys[my_key]
        except (AttributeError, KeyError, ValueError):
            pass

class CollectTask(SearchAndTravelTask):
    """ for minions only """
    impassable = 1

    @property
    def targets(self):
        return transport_map.keys()

    def enter(self):
        if len(self.sprite.carried) >= 1:
            self.fail()
        else:
            super(CollectTask, self).enter()

    def exit(self):
        super(CollectTask, self).exit()
        self.parent.queue(MineTask(sprite=self.sprite, duration=200.0, mine=8))

class DepositTask(SearchAndTravelTask):
    """ for minions only """
    impassable = 1

    # a bug causes the sprite to pick up an illeagal tile...
    # i haven't figured out what causes it yet...
    @property
    def targets(self):
        spr = self.sprite
        spr.carried = [ i for i in spr.carried if i in transport_map.keys() ]
        return set(transport_map[i] for i in spr.carried)

    def exit(self):
        super(DepositTask, self).exit()
        task = DropCarriedTask(sprite=self.sprite)
        self.parent.queue(task)


class DropCarriedTask(Task):
    empty = BARREN

    force = {
        FARM: 2,
    }

    def update(self, time):
        spr = self.sprite

        if len(spr.carried) > 0:
            coords = map(int, spr.position)[:2]
            tile, value = spr.level.get_tile(coords)

            depo_map = {v:k for k, v in transport_map.items()}
            try:
                target = depo_map[tile]
            except KeyError:
                # happens if a minion mines BARREN or some other tile
                self.sprite.carried = []
                self.done()
                return

            to_remove = []
            for i, carried in enumerate(self.sprite.carried):
                if carried == target:
                    to_remove.append(i)
                    v = value + self.force[target]
                    if v > 15:
                        spr.level.set_tile(coords, self.empty)
                        self.filled(coords, target)
                    else:
                        spr.level.set_tile(coords, tile, v)

            for i in to_remove:
                spr.carried.pop(i)

        else:
            self.done()

    def filled(self, coords, tile):
        if tile == FARM:
            from gameobjects import Minion
            m = Minion(self.sprite.groups()[0])
            m.position = self.sprite.position.copy()

    def exit(self):
        try:
            my_key, dest = getattr(self.parent, "tile_lock")
            ExclusiveKeys[my_key].remove(dest)
            if len(ExclusiveKeys[my_key]) == 0:
                del ExclusiveKeys[my_key]
        except (AttributeError, KeyError, ValueError):
            pass

class MissileMoveTask(Task):
    def update(self, time):
        spr = self.sprite
        spr.position -= spr.move_vector * spr.travel_speed
        if abs(spr.position - (10,10,0)) > 15:
            spr.kill()

        spr = self.sprite
        groups = spr.groups()
        if groups:
            enemies = groups[0].of_class(self.target)
            
            for e in enemies:
                if abs(spr.position - e.position) < .35:
                    e.hp -= 1
                    spr.kill()
                    break

class HuntTask(Task):
    def update(self, time):
        spr = self.sprite
        victim = self.parent.victim

        if victim is None:
            group = spr.groups()[0]
            victims = list(group.of_class(self.target))
            if victims:
                victim = random.choice(victims)
                self.parent.victim = victim
            else:
                self.done()
                return

        spr.move_vector = spr.position - victim.position
        spr.move_vector.normalize()
        spr.position -= spr.move_vector * spr.travel_speed

        if abs(spr.position - victim.position) < .25:
            victim.stuck = 1
            victim.position = spr.position + (.05, .05, .25)
            self.done()

    def enter(self):
        self.parent.victim = None
