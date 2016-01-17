from MemoryModel import *


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

        if minpos and minhp <= 2666:
            mm.grow_plant(Plant.PUMPKIN, *minpos)


class BalloonTracker:
    def __init__(self):
        pass

    def update(self, mm):
        for zombie in mm.zombies:
            if zombie.type != Zombie.BALLOON:
                continue

            if zombie.x <= 50:
                for row in range(0, 6):
                    for col in range(0, 9):
                        if mm.grow_plant(Plant.CLOVER, row, col):
                            return


class SquashLauncher:
    def __init__(self):
        self.row = 0

    def update(self, mm):
        if mm.jackExploding:
            return

        mm.grow_plant(Plant.SQUASH, self.row, 5, True) or mm.grow_plant(Plant.SQUASH, self.row, 4, True)

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


class CherryAndJalapenoLauncher:
    ICE_PATH_LIMIT = [108, 188, 268, 348, 428, 508, 588, 668, 751]

    def __init__(self, col=5):
        self.col = col

    def update(self, mm):
        if not mm.cards[Plant.CHERRY].usable or not mm.cards[Plant.JALAPENO].usable or mm.jackExploding:
            return

        mm.grow_plant(Plant.CHERRY, 1, self.col, True)
        if mm.icePath[5] >= CherryAndJalapenoLauncher.ICE_PATH_LIMIT[self.col]:
            mm.grow_plant(Plant.JALAPENO, 5, self.col, True)
        else:
            mm.grow_plant(Plant.JALAPENO, 5, 4, True)
        mm.fodderOperator.pause(mm, 105)
        mm.memoryObserver.remove(self)


class DoomLauncher:
    def __init__(self, row=None, col=None, imitater=False):
        self.row = row
        self.col = col
        self.imitater = imitater

    def update(self, mm):
        def use_doom(row, col):
            if row in [2, 3] and not mm.grow_plant(Plant.LILY_PAD, row, col) or mm.jackExploding:
                return False

            if not self.imitater:
                mm.grow_plant(Plant.DOOM_SHROOM, row, col)
                mm.fodderOperator.pause(mm, 105)
                mm.nextDoomExplodeAt = mm.timestamp + 100
            else:
                mm.grow_plant(Plant.IMITATER, row, col)
                mm.nextDoomExplodeAt = mm.timestamp + 420

            mm.memoryObserver.remove(self)
            return True

        if self.imitater and not mm.cards[Plant.IMITATER].usable:
            return
        elif not self.imitater and not mm.cards[Plant.DOOM_SHROOM].usable:
            return

        if self.row is not None and self.col is not None:
            use_doom(self.row, self.col)
        else:
            if not mm.cards[Plant.LILY_PAD].usable:
                return

            for row in range(2, 4):
                for col in range(6, 9):
                    if use_doom(row, col):
                        return


class ShoreDoomLauncher:
    def __init__(self, imitater=False):
        self.imitater = imitater

    def update(self, mm):
        if not mm.cards[Plant.SQUASH].usable or not mm.cards[Plant.DOOM_SHROOM].usable or mm.jackExploding:
            return

        for row in [1, 4]:
            if row == 1:
                cmax = 8
            else:
                cmax = 9

            if self.imitater:
                cmax = 7

            for col in reversed(range(6, cmax)):
                if self.imitater:
                    ok = mm.grow_plant(Plant.IMITATER, row, col)
                else:
                    ok = mm.grow_plant(Plant.DOOM_SHROOM, row, col)

                if ok:
                    if row == 1:
                        squash_row = 5
                    else:
                        squash_row = 0

                    for squash_col in reversed(range(0, 9)):
                        if mm.grow_plant(Plant.SQUASH, squash_row, squash_col):
                            if mm.nZombieWaves != 20:
                                mm.strategy.squashLauncher.start(mm)
                            mm.memoryObserver.remove(self)
                            return

                    mm.MemoryObserver.remove(self)
                    return


class ShoreImitaterDoomLauncher:
    def __init__(self):
        pass

    def update(self, mm):
        if not mm.cards[Plant.SQUASH].usable or not mm.cards[Plant.IMITATER].usable or\
                not mm.cards[Plant.ICE_SHROOM].usable or mm.jackExploding:
            return

        ok = False
        for row in range(0, 6):
            for col in range(0, 9):
                ok = mm.grow_plant(Plant.ICE_SHROOM, row, col)
                if ok:
                    mm.MemoryObserver.remove(self)
                    break

            if ok:
                break

        mm.set_timeout(100, lambda mm: mm.memoryObserver.append(ShoreDoomLauncher(True)))


class ImitaterDoomLauncher:
    def __init__(self, row=None, col=None):
        self.row = row
        self.col = col

    def update(self, mm):
        if not mm.cards[Plant.ICE_SHROOM].usable or mm.jackExploding:
            return

        if self.col is None and self.row is None:
            ok = False
            for row in range(2, 4):
                for col in range(6, 9):
                    if mm.gridStatus[row][col]:
                        ok = True
                        break

                if ok:
                    break

            if not ok:
                return

        for row in range(0, 6):
            for col in range(0, 9):
                mm.grow_plant(Plant.ICE_SHROOM, row, col)

        mm.memoryObserver.remove(self)
        mm.set_timeout(100, lambda mm: mm.memoryObserver.append(DoomLauncher(self.row, self.col, True)))
        mm.fodderOperator.pause(mm, 525)


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
