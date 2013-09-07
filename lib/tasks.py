import collections
import random

from euclid import Vector3
from pathfinding import aStar
from const import *
import context



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

class StealStockpileTask(Task):
    pass

class MineTask(Task):
    complete = 150.0
    empty = BARREN
    target = FARM

    def update(self, time):
        self._progress += time
        self.progress = self._progress / self.complete

        if self.progress >= 1.0:
            spr = self.sprite
            x, y, z = map(int, spr.position)
            t, v = spr.level.get_tile((x, y))
            if v >= 15:
                spr.level.set_tile((x, y), self.empty)
            else:
                spr.level.set_tile((x, y), t, v+1)
            spr.carried += 1
            self.done()

    def enter(self):
        x, y, z = map(int, self.sprite.position)
        if not self.sprite.level.test_type((x, y), self.target):
            self.done()

        self._progress = 0.0
        self.progress = 0.0

    def exit(self):
        my_key, dest = getattr(self.parent, "release_key", (None, None))
        if my_key == self:
            try:
                del ExclusiveKeys[my_key]
            except KeyError:
                pass
        elif my_key is not None:
            try:
                ExclusiveKeys[my_key].remove(dest)
            except ValueError:
                print "failed to remove", dest
                pass
            except AttributeError:
                pass
            except:
                raise

class ExcavateTask(MineTask):
    complete = 75.0
    empty = BARREN
    target = REGOLITH

class FarmTask(MineTask):
    complete = 150.0
    empty = BARREN
    target = FARM

class IntervalTask(Task):
    interval = 100.0
    show = True

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

class ChompMinion(IntervalTask):
    interval = 100.0
    show = False

    def work(self):
        spr = self.sprite
        victim = self.parent.victim

        if victim is None:
            self.done()
            return

        victim.hp -= 1
        if victim.hp <= 0:
            self.parent.victim = None
            self.done()

class ShootEnemiesTask(IntervalTask):
    interval = 100.0
    spread = 3

    def test(self):
        return list(self.sprite.groups()[0].of_class(self.target))

    def work(self):
        from gameobjects import Missile

        spr = self.sprite
        group = spr.groups()[0]

        shot = 0
        for e in group.of_class(self.target):
            if shot < self.spread:
                shot += 1
                m = Missile(spr.level, target=self.target)
                m.position = spr.position.copy()
                d = spr.position - e.position
                d.normalize()
                m.move_vector = d * m.travel_speed
                group.add(m)

ExclusiveKeys = collections.defaultdict(list)

class SearchAndTravelTask(Task):
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
            blacklist = ExclusiveKeys[self.my_key]
        self.dest, dist = spr.level.nearest_tile(spr.position, self.tile_type, blacklist)

        if self.dest is not None:
            self.path = aStar(tuple(map(round, spr.position[:2])), tuple(self.dest), (20, 20))
            ExclusiveKeys[self.my_key].append(tuple(self.dest))

    def enter(self):
        self.path = None
        self.my_key = getattr(self, "key", None)

    def exit(self):
        try:
            self.parent.release_key = (self.my_key, self.dest)
        except:
            pass

class DropCarriedTask(Task):
    def update(self, time):
        spr = self.sprite
        if spr.carried > 0:
            tile, value = spr.level.get_tile(map(int, spr.position)[:2])
            if tile in (ORIGIN, STOCKPILE):
                spr.carried -= 1
                #player.regolith += 1
            else:
                self.done()
        else:
            #s = Shuttle(spr.level)
            #s.position = spr.position.copy()
            #spr.groups()[0].add(s)
            self.done()

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

