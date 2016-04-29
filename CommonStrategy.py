from MemoryModel import *


def _ensure_giga_and_zomboni(fn):
    def ret(self, mm):
        if mm.hasZombie[Zombie.GIGA_GARGANTUAR] or mm.hasZombie[Zombie.GARGANTUAR]:
            fn(self, mm)
            return

        for row in [0, 5]:
            if mm.minZombieX[row][Zombie.ZOMBONI] is not None:
                fn(self, mm)
                return

        self._finish(mm)

    return ret


def _pool_doom_grid_timeout(mm):
    min_timeout = 2147483647

    status = [[True, True, True], [True, True, True]]

    for i in [2, 3]:
        for j in [6, 7, 8]:
            status[i - 2][j - 6] = mm.gridStatus[i][j]

    for crater in mm.craters:
        if crater.row in [2, 3] and\
                        crater.col in [6, 7, 8] and\
                        crater.timeout > 0:
            status[crater.row - 2][crater.col - 6] = False
            min_timeout = min(min_timeout, crater.timeout)

    for a in status:
        for ok in a:
            if ok:
                return 0

    return min_timeout


class PumpkinFixer:
    def __init__(self):
        pass

    def update(self, mm):
        if not mm.cards[Plant.PUMPKIN].usable:
            return

        minhp = 4000
        minpos = None
        status = [[False for j in range(0, 9)] for i in range(0, 6)]
        for plant in mm.plants:
            if plant.type != Plant.PUMPKIN:
                continue

            if plant.hp < minhp:
                minhp = plant.hp
                minpos = (plant.row, plant.col)

            status[plant.row][plant.col] = True

        for row in range(0, 6):
            if row in [0, 1, 4, 5]:
                r = range(0, 3)
            else:
                r = range(4, 6)

            for col in r:
                if not status[row][col]:
                    mm.grow_plant(Plant.PUMPKIN, row, col)
                    return

        if minpos is not None and minhp <= 2666:
            mm.grow_plant(Plant.PUMPKIN, *minpos)


class BalloonTracker:
    def __init__(self):
        pass

    def update(self, mm):
        for row in range(0, 6):
            if mm.minZombieX[row][Zombie.BALLOON] is not None and\
               mm.minZombieX[row][Zombie.BALLOON] <= 50:
                    for r in [4, 1, 0, 5, 2, 3]:
                        for col in range(0, 9):
                            if mm.grow_plant(Plant.CLOVER, r, col):
                                return


class SquashLauncher:
    def __init__(self):
        self.row = 0

    def update(self, mm):
        if mm.jackExploding:
            return

        if not mm.hasZombie[Zombie.GARGANTUAR] and\
           not mm.hasZombie[Zombie.GIGA_GARGANTUAR] and\
           not mm.hasZombie[Zombie.ZOMBONI]:
            return

        if mm.grow_plant(Plant.SQUASH, self.row, 5, True) or\
                mm.grow_plant(Plant.SQUASH, self.row, 4, True):

            if self.row == 0:
                self.row = 5
            else:
                self.row = 0

    def start(self, mm):
        if self not in mm.memoryObserver:
            mm.memoryObserver.append(self)

    def stop(self, mm):
        while self in mm.memoryObserver:
            mm.memoryObserver.remove(self)


class RegularLauncher:
    def _finish(self, mm):
        for fn in self._finishedCallback:
            fn(mm)

        self.finished = True
        mm.memoryObserver.remove(self)
        self._finishedCallback = []


class CherryAndJalapenoLauncher(RegularLauncher):
    ICE_PATH_LIMIT = [108, 188, 268, 348, 428, 508, 588, 668, 751]

    def __init__(self, col=5):
        self.col = col
        self.finished = False
        self._finishedCallback = []

    def on_finished(self, fn):
        self._finishedCallback.append(fn)

    @staticmethod
    def is_ready(mm):
        return mm.cards[Plant.CHERRY].usable and mm.cards[Plant.JALAPENO].usable

    @staticmethod
    def time_remain(mm):
        if CherryAndJalapenoLauncher.is_ready(mm):
            return 0
        else:
            if mm.cards[Plant.CHERRY].usable:
                return mm.cards[Plant.JALAPENO].timeRemain
            else:
                if mm.cards[Plant.JALAPENO].usable:
                    return mm.cards[Plant.CHERRY].timeRemain
                else:
                    return max(mm.cards[Plant.CHERRY].timeRemain, mm.cards[Plant.JALAPENO].timeRemain)

    @_ensure_giga_and_zomboni
    def update(self, mm):
        if not CherryAndJalapenoLauncher.is_ready(mm) or mm.jackExploding:
            return

        if not mm.hasZombie[Zombie.GIGA_GARGANTUAR] and\
           not mm.hasZombie[Zombie.GARGANTUAR] and\
           mm.maxZombieX[0][Zombie.ZOMBONI] is not None and\
           mm.maxZombieX[0][Zombie.ZOMBONI] >= 603.25:
            return

        if self.col == 5:
            mm.grow_plant(Plant.CHERRY, 1, self.col, True)
        else:
            for row in range(0, 2):
                for col in reversed(range(7, 9)):
                    mm.grow_plant(Plant.CHERRY, row, col, True)

        if mm.icePath[5] >= CherryAndJalapenoLauncher.ICE_PATH_LIMIT[self.col]:
            mm.grow_plant(Plant.JALAPENO, 5, self.col, True)
        elif mm.icePath[4] >= CherryAndJalapenoLauncher.ICE_PATH_LIMIT[4]:
            mm.grow_plant(Plant.JALAPENO, 5, 4, True)
        else:
            mm.grow_plant(Plant.JALAPENO, 5, 3, True)

        mm.fodderOperator.pause(mm, 105)
        self._finish(mm)


class DoomLauncher(RegularLauncher):
    def __init__(self, row=None, col=None, imitater=False):
        self.row = row
        self.col = col
        self.imitater = imitater

        self.finished = False
        self._finishedCallback = []

        self.delay = False
        self.delayTo = None

    @staticmethod
    def is_ready(mm, imitater=False):
        if not mm.cards[Plant.LILY_PAD].usable:
            return False

        if _pool_doom_grid_timeout(mm) != 0:
            return False

        if imitater:
            return mm.cards[Plant.IMITATER].usable
        else:
            return mm.cards[Plant.DOOM_SHROOM].usable

    @staticmethod
    def time_remain(mm, imitatier=False):
        if DoomLauncher.is_ready(mm, imitatier):
            return 0

        cmp = [0, _pool_doom_grid_timeout(mm)]

        if imitatier:
            doom = Plant.IMITATER
        else:
            doom = Plant.DOOM_SHROOM

        if not mm.cards[doom].usable:
            cmp.append(mm.cards[doom].timeRemain)

        if not mm.cards[Plant.LILY_PAD].usable:
            cmp.append(mm.cards[Plant.LILY_PAD].timeRemain)

        return max(cmp)

    def set_delay(self, mm):
        if not self.imitater:
            self.delayTo = mm.spawnedAt + 260
            print("Delay to: " + str(self.delayTo))

    def on_finished(self, fn):
        self._finishedCallback.append(fn)

    @_ensure_giga_and_zomboni
    def update(self, mm):
        def use_doom(row, col):
            if mm.jackExploding:
                return False

            if row in [2, 3] and not mm.grow_plant(Plant.LILY_PAD, row, col):
                if row == 8 and col == 3:
                    mm.update_plant_info()

                    ok = False
                    for plant in mm.plants:
                        if plant.type == Plant.LILY_PAD and plant.row in [2, 3] and plant.col in [6, 7, 8] and\
                                        plant.hp > 0:
                            ok = True
                            row = plant.row
                            col = plant.col
                            break

                    if not ok:
                        return False
                else:
                    return False

            if not self.imitater:
                mm.grow_plant(Plant.DOOM_SHROOM, row, col)
                mm.fodderOperator.pause(mm, 105)
                mm.nextDoomExplodeAt = mm.timestamp + 100
            else:
                mm.grow_plant(Plant.IMITATER, row, col)
                mm.nextDoomExplodeAt = mm.timestamp + 420

            return True

        if not self.is_ready(mm, self.imitater):
            return

        if self.delayTo is not None and self.delayTo > mm.timestamp:
            return

        if self.row is not None and self.col is not None and use_doom(self.row, self.col):
                self._finish(mm)
        else:
            for row in range(2, 4):
                for col in range(6, 9):
                    if use_doom(row, col):
                        self._finish(mm)
                        return


class ShoreDoomLauncher(RegularLauncher):
    def __init__(self, row, imitater=False, require_squash=True):
        self.row = row

        if imitater or self.row == 0:
            self.colRange = range(6, 8)
        else:
            self.colRange = range(6, 9)

        self.imitater = imitater
        self.require_squash = require_squash

        self.finished = False
        self._finishedCallback = []

    def on_finished(self, fn):
        self._finishedCallback.append(fn)

    def is_ready(self, mm):
        if self.require_squash and not mm.cards[Plant.SQUASH].usable:
            return False

        if self.imitater:
            if not mm.cards[Plant.IMITATER].usable:
                return False
        elif not mm.cards[Plant.DOOM_SHROOM].usable:
            return False

        for i in self.colRange:
            if mm.gridStatus[self.row][i]:
                return True

        return False

    def time_remain(self, mm):
        if self.is_ready(mm):
            return 0

        cmp = [0]

        no_grid = True
        for i in self.colRange:
            if mm.gridStatus[self.row][i]:
                no_grid = False
                break

        if no_grid:
            grid_cmp = [2147483647 for i in self.colRange]

            for crater in mm.craters:
                if crater.row == self.row and crater.col in self.colRange:
                    grid_cmp[crater.col - 6] = crater.timeout

            if mm.icePath[self.row] < 800:
                for i in self.colRange:
                    if mm.icePath[self.row] < CherryAndJalapenoLauncher.ICE_PATH_LIMIT[i]:
                        grid_cmp[i - 6] = min(grid_cmp[i - 6], mm.icePathCountdown[self.row])

            cmp.append(min(grid_cmp))

        if self.require_squash and not mm.cards[Plant.SQUASH].usable:
            cmp.append(mm.cards[Plant.SQUASH].timeRemain)

        if self.imitater:
            if not mm.cards[Plant.IMITATER].usable:
                cmp.append(mm.cards[Plant.IMITATER].timeRemain)
        elif not mm.cards[Plant.DOOM_SHROOM].usable:
            cmp.append(mm.cards[Plant.DOOM_SHROOM].timeRemain)

        return max(cmp)

    @_ensure_giga_and_zomboni
    def update(self, mm):
        if not self.is_ready(mm) or mm.jackExploding:
            return

        for col in reversed(self.colRange):
            if self.imitater:
                ok = mm.grow_plant(Plant.IMITATER, self.row, col)
            else:
                ok = mm.grow_plant(Plant.DOOM_SHROOM, self.row, col)

            if not ok:
                continue

            if self.require_squash:
                if self.row in [0, 1]:
                    squash_row = 5
                else:# 4
                    squash_row = 0

                for squash_col in reversed(range(0, 9)):
                    if mm.grow_plant(Plant.SQUASH, squash_row, squash_col):
                        if mm.nZombieWaves != 20:
                            mm.strategy.squashLauncher.start(mm)

                        break

            self._finish(mm)
            return


class ShoreImitaterDoomLauncher(RegularLauncher):
    def __init__(self, row, require_squash=True):
        self._iceUsed = False
        self._shoreDoomLauncher = ShoreDoomLauncher(row, True, require_squash=True)

        self.row = row
        self.require_squash = require_squash
        self.finished = False
        self._finishedCallback = []

    def on_finished(self, fn):
        self._finishedCallback.append(fn)

    def is_ready(self, mm):
        return mm.cards[Plant.ICE_SHROOM].usable and self._shoreDoomLauncher.is_ready(mm)

    def time_remain(self, mm):
        if mm.cards[Plant.ICE_SHROOM].usable:
            return self._shoreDoomLauncher.time_remain(mm)
        else:
            print(mm.cards[Plant.ICE_SHROOM].timeRemain)
            return max(mm.cards[Plant.ICE_SHROOM].timeRemain, self._shoreDoomLauncher.time_remain(mm))

    @_ensure_giga_and_zomboni
    def update(self, mm):
        if self._iceUsed:
            if self._shoreDoomLauncher.finished:
                self._finish(mm)
            return

        if not mm.cards[Plant.SQUASH].usable or not mm.cards[Plant.IMITATER].usable or\
                not mm.cards[Plant.ICE_SHROOM].usable or mm.jackExploding:
            return

        for row in range(0, 6):
            for col in range(0, 9):
                self._iceUsed = mm.grow_plant(Plant.ICE_SHROOM, row, col)
                if self._iceUsed:
                    mm.memoryObserver.append(self._shoreDoomLauncher)
                    return


class ImitaterDoomLauncher(RegularLauncher):
    def __init__(self, row=None, col=None):
        self.row = row
        self.col = col

        self._iceUsed = False
        self.finished = False
        self.delay = False

        self._finishedCallback = []

        self._doomLauncher = None

    def set_delay(self, mm):
        self.delay = True

    def on_finished(self, fn):
        self._finishedCallback.append(fn)

    @staticmethod
    def is_ready(mm):
        if not(mm.cards[Plant.LILY_PAD].usable or mm.cards[Plant.LILY_PAD].timeRemain < 100):
            return False

        if not(mm.cards[Plant.IMITATER].usable or mm.cards[Plant.IMITATER].timeRemain < 100):
            return False

        if _pool_doom_grid_timeout(mm) > 100:
            return False

        return mm.cards[Plant.ICE_SHROOM].usable

    @staticmethod
    def time_remain(mm):
        if ImitaterDoomLauncher.is_ready(mm):
            return 0
        else:
            cmp = [0, _pool_doom_grid_timeout(mm) - 100]

            if not mm.cards[Plant.IMITATER].usable:
                cmp.append(mm.cards[Plant.IMITATER].timeRemain - 100)

            if not mm.cards[Plant.LILY_PAD].usable:
                cmp.append(mm.cards[Plant.LILY_PAD].timeRemain - 100)

            if not mm.cards[Plant.ICE_SHROOM].usable:
                cmp.append(mm.cards[Plant.ICE_SHROOM].timeRemain)

            return max(cmp)

    @_ensure_giga_and_zomboni
    def update(self, mm):
        if self._iceUsed:
            if self._doomLauncher.finished:
                self._finish(mm)
            else:
                return

        if not mm.cards[Plant.ICE_SHROOM].usable or mm.jackExploding:
            return

        if self.col is None and self.row is None:
            ok = False
            for row in range(2, 4):
                for col in range(6, 9):
                    ok = ok or mm.gridStatus[row][col]

            if not ok:
                return

        for row in range(0, 6):
            for col in range(0, 9):
                if mm.grow_plant(Plant.ICE_SHROOM, row, col):
                    self._iceUsed = True

                    self._doomLauncher = DoomLauncher(self.row, self.col, True)
                    if self.delay:
                        self._doomLauncher.set_delay(mm)

                    mm.set_timeout(100, lambda mm: mm.memoryObserver.append(self._doomLauncher))
                    mm.fodderOperator.pause(mm, 525)

                    return


class FodderOperator:
    def __init__(self):
        pass

    def update(self, mm):
        minx = 2147483647
        min_row = None

        for zombie in mm.zombies:
            if zombie.type not in [Zombie.GARGANTUAR, Zombie.GIGA_GARGANTUAR] or \
               zombie.hp <= 130 and zombie.row in [0, 5] or \
               zombie.hp <= 1000 and zombie.x >= 420 and zombie.row in [1, 4]:
                continue

            if zombie.x < minx:
                minx = zombie.x
                min_row = zombie.row

        if minx <= 515:
            mm.grow_plant(Plant.FUME_SHROOM, min_row, 5)
            mm.grow_plant(Plant.CLOVER, min_row, 5)

    def pause(self, mm, cs):
        if self in mm.memoryObserver:
            mm.memoryObserver.remove(self)
        mm.set_timeout(cs, lambda mm: mm.memoryObserver.append(self))


class FumeFixer:
    def __init__(self):
        pass

    def update(self, mm):
        if not mm.cards[Plant.FUME_SHROOM].usable:
            return

        for row in [1, 4, 0, 5]:
            for col in [3, 4]:
                if mm.gridStatus[row][col] and mm.grow_plant(Plant.FUME_SHROOM, row, col):
                    return


class ItemCollector:
    def __init__(self):
        pass

    def update(self, memory_model):
        mouse_reset()
        for item in memory_model.items:
            if item.y >= 90:
                mouse_left_click(item.x, item.y)
