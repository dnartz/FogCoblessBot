from MemoryModel import *
from CommonStrategy import *


def _record_deco(fn):
    def ret(self, mm):
        self.spawnHandler.append(ret)
        fn(self, mm)

    return ret


class GigaStrategy:
    def __init__(self):
        self.spawnHandler = [
        ]
        self.squashLauncher = SquashLauncher()

    @_record_deco
    def regular_doom(self, mm):
        mm.set_timeout(1100, lambda mm: mm.memoryObserver.append(DoomLauncher()))

    @_record_deco
    def regular_imitater_doom(self, mm):
        mm.set_timeout(1200, lambda mm: mm.memoryObserver.append(ImitaterDoomLauncher()))

    @_record_deco
    def regular_cherry_and_jalapeno(self, mm):
        mm.set_timeout(1100, lambda mm: mm.memoryObserver.append(CherryAndJalapenoLauncher()))

    @_record_deco
    def shore_doom(self, mm):
        mm.set_timeout(330, lambda mm: mm.memoryObserver.append(ShoreDoomLauncher()))

    @_record_deco
    def shore_imitater_doom(self, mm):
        mm.set_timeout(330, lambda mm: mm.memoryObserver.append(ImitaterDoomLauncher()))

    @_record_deco
    def cherry_and_jalapeno_front(self, mm):
        if mm.nZombieWaves == 1:
            mm.set_timeout(330, lambda mm: mm.memoryObserver.append(CherryAndJalapenoLauncher(8)))
        else:  # 第10波
            mm.set_timeout(330, lambda mm: mm.memoryObserver.append(CherryAndJalapenoLauncher(7)))

    def select_regular_operation(self, ignore_doom=False):
        mm = MemoryModel.get_instance()

        if not ignore_doom and mm.nextDoomExplodeAt is not None:
            print("time diff: " + str(mm.nextDoomExplodeAt - mm.timestamp))
            if mm.nextDoomExplodeAt - mm.timestamp >= 190:
                print("canceled")
            return None

        if mm.cards[Plant.CHERRY].usable and mm.cards[Plant.JALAPENO].usable:
            print(str(mm.nZombieWaves) + ": return cj usable")
            return self.regular_cherry_and_jalapeno
        elif mm.cards[Plant.DOOM_SHROOM].usable:
            print(str(mm.nZombieWaves) + ": return doom usable")
            return self.regular_doom
        elif mm.cards[Plant.IMITATER].usable:
            print(str(mm.nZombieWaves) + ": return imitater doom usable")
            return self.regular_imitater_doom

        min_type = Plant.CHERRY
        min_remain = mm.cards[Plant.CHERRY].timeRemain
        min_method = self.regular_cherry_and_jalapeno

        if mm.cards[Plant.DOOM_SHROOM].timeRemain < min_remain:
            min_type = Plant.DOOM_SHROOM
            min_remain = mm.cards[Plant.DOOM_SHROOM].timeRemain
            min_method = self.regular_doom

        if mm.cards[Plant.IMITATER].timeRemain < min_remain:
            min_type = Plant.IMITATER
            min_remain = mm.cards[Plant.IMITATER].timeRemain
            min_method = self.regular_imitater_doom

        result = str(mm.nZombieWaves) + ": not ready:"
        if min_type == Plant.CHERRY:
            result += "cj"
        elif min_type == Plant.DOOM_SHROOM:
            result += "DOOM"
        else:
            result += "imitater"

        result += ":" + str(min_remain)
        print(result)
        return min_method

    def select_specific_operation(self):
        min_method = self.select_regular_operation(ignore_doom=True)
        if min_method == self.regular_cherry_and_jalapeno:
            min_method = self.cherry_and_jalapeno_front
        elif min_method == self.regular_doom:
            min_method = self.shore_doom
        else:
            min_method = self.shore_imitater_doom

        return min_method

    def get_launcher(self, min_method):
        if min_method == self.shore_doom:
            return ShoreDoomLauncher
        elif min_method == self.shore_imitater_doom:
            return ShoreImitaterDoomLauncher
        elif min_method in [self.cherry_and_jalapeno_front, self.regular_cherry_and_jalapeno]:
            return CherryAndJalapenoLauncher
        elif min_method == self.regular_doom:
            return DoomLauncher
        elif min_method == self.regular_imitater_doom:
            return ImitaterDoomLauncher

    def handle_spawn(self, mm):
        if mm.nZombieWaves in [1, 10]:
            self.wave1_10(mm)
        elif mm.nZombieWaves in [2, 11]:
            self.wave2_11(mm)
        elif mm.nZombieWaves in range(3, 9) or mm.nZombieWaves in range(12, 19):
            self.regular_wave(mm)
        elif mm.nZombieWaves in [9, 19]:
            self.wave9(mm)
        elif mm.nZombieWaves == 20:
            self.wave20(mm)

    def wave1_10(self, mm):
        min_method = self.select_specific_operation()
        if min_method:
            min_method(mm)

    def wave2_11(self, mm):
        min_method = self.select_regular_operation()
        if min_method is None:
            return

        if mm.nZombieWaves == 2 and self.spawnHandler[0] == GigaStrategy.cherry_and_jalapeno_front:
            if min_method == self.regular_doom:
                return self.shore_doom(mm)
            else:
                return self.shore_imitater_doom(mm)

        return min_method(mm)

    def regular_wave(self, mm):
        if mm.nZombieWaves in [3, 12]:
            self.squashLauncher.start(mm)

        min_method = self.select_regular_operation()
        if min_method is not None:
            min_method(mm)

    def wave9(self, mm):
        self.regular_wave(mm)
        self.squashLauncher.stop(mm)
        if mm.hasGigaCurrentWave:
            mm.set_timeout(2000, lambda mm: mm.memoryObserver.append(CherryAndJalapenoLauncher()))

    def wave20(self, mm):
        def kill_giga(mm):
            if mm.hasGigaCurrentWave:
                mm.memoryObserver.append(self.get_launcher(self.select_regular_operation(ignore_doom=True))())

        self.select_specific_operation()(mm)
        mm.set_timeout(1000, kill_giga)
        mm.set_timeout(1100, lambda mm: mm.memoryObserver.append(
            self.get_launcher(self.select_specific_operation())()))
