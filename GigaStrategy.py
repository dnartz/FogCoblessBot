from MemoryModel import *
from CommonStrategy import *


def _record_deco(fn):
    def ret(self, *args):
        mm = MemoryModel.get_instance()

        if len(self.launcherUsed) > 0 and\
                (isinstance(self.launcherUsed[-1], DoomLauncher) or
                 isinstance(self.launcherUsed[-1], ImitaterDoomLauncher)) and\
                self.launcherUsed[-1] in mm.memoryObserver:
            self.launcherUsed[-1].set_delay(args[-1])
            print('Handle by previous wave.')

        else:
            self.spawnHandler.append(ret)
            fn(self, *args)

    return ret


class GigaStrategy:
    def __init__(self):
        self.spawnHandler = []
        self.launcherUsed = []
        self.squashLauncher = SquashLauncher()

        self.lastRegularAttack = None

        self.regularLauncherIndex = {
            CherryAndJalapenoLauncher: self.regular_cherry_and_jalapeno,
            ImitaterDoomLauncher: self.regular_imitater_doom,
            DoomLauncher: self.regular_doom
        }

        self.regularCandidateList = [CherryAndJalapenoLauncher, DoomLauncher, ImitaterDoomLauncher]

    @_record_deco
    def regular_doom(self, mm):
        if DoomLauncher in self.regularCandidateList:
            self.regularCandidateList.remove(DoomLauncher)
        else:
            return

        last = DoomLauncher()
        last.on_finished(lambda mm: self.regularCandidateList.append(DoomLauncher))

        self.launcherUsed.append(last)
        mm.set_timeout(1100, lambda mm: mm.memoryObserver.append(last))

    @_record_deco
    def regular_imitater_doom(self, mm):
        if ImitaterDoomLauncher in self.regularCandidateList:
            self.regularCandidateList.remove(ImitaterDoomLauncher)
        else:
            return

        last = ImitaterDoomLauncher()
        last.on_finished(lambda mm: self.regularCandidateList.append(ImitaterDoomLauncher))

        self.launcherUsed.append(last)
        mm.set_timeout(1200, lambda mm: mm.memoryObserver.append(last))

    @_record_deco
    def regular_cherry_and_jalapeno(self, mm):
        if CherryAndJalapenoLauncher in self.regularCandidateList:
            self.regularCandidateList.remove(CherryAndJalapenoLauncher)
        else:
            return

        last = CherryAndJalapenoLauncher()
        last.on_finished(lambda mm: self.regularCandidateList.append(CherryAndJalapenoLauncher))

        self.launcherUsed.append(last)
        mm.set_timeout(1100, lambda mm: mm.memoryObserver.append(last))

    @_record_deco
    def shore_doom(self, col, require_squash, mm):
        self.launcherUsed.append(ShoreDoomLauncher(col, False, require_squash))
        mm.set_timeout(330, lambda mm: mm.memoryObserver.append(self.launcherUsed[-1]))

    @_record_deco
    def shore_imitater_doom(self, col, require_squash, mm):
        self.launcherUsed.append(ShoreImitaterDoomLauncher(col, require_squash))
        print(str(mm.nZombieWaves) + 'shore time remain: ' + str(self.launcherUsed[-1].time_remain(mm)))
        if mm.nZombieWaves not in [2, 11]:
            mm.set_timeout(330, lambda mm: mm.memoryObserver.append(self.launcherUsed[-1]))
        else:
            mm.set_timeout(0, lambda mm: mm.memoryObserver.append(self.launcherUsed[-1]))

    @_record_deco
    def cherry_and_jalapeno_front(self, mm):
        if mm.nZombieWaves == 1:
            self.launcherUsed.append(CherryAndJalapenoLauncher(8))
        else:  # 第10波
            self.launcherUsed.append(CherryAndJalapenoLauncher(7))

        mm.set_timeout(0, lambda mm: mm.memoryObserver.append(self.launcherUsed[-1]))

    def select_regular_operation(self):
        mm = MemoryModel.get_instance()

        for launcher in self.regularCandidateList:
            if launcher.is_ready(mm):
                return self.regularLauncherIndex[launcher](mm)

        min_remain = 2147483647
        min_method = None
        for launcher in self.regularCandidateList:
            if launcher.time_remain(mm) < min_remain:
                min_remain = launcher.time_remain(mm)
                min_method = self.regularLauncherIndex[launcher]

        if min_method:
            min_method(mm)
        else:
            print("No candinate.")

    def select_specific_operation(self, col, mm, require_squash=True):
        cmp = [
            CherryAndJalapenoLauncher.time_remain(mm),
            ShoreImitaterDoomLauncher(col, require_squash).time_remain(mm),
            ShoreDoomLauncher(col, require_squash).time_remain(mm),
        ]

        t_min = min(cmp)
        print(t_min)

        if t_min > 300:
            self.select_regular_operation()
            return

        if t_min == cmp[0]:
            print(str(mm.nZombieWaves) + " Special: Cherry and Jalapeno")
            self.cherry_and_jalapeno_front(mm)
        elif t_min == cmp[1]:
            print(str(mm.nZombieWaves) + " Special: shore Imitater Doom-Shroom")
            self.shore_imitater_doom(col, require_squash, mm)
        else:
            print(str(mm.nZombieWaves) + " Special: shore Doom-Shroom")
            self.shore_doom(col, require_squash, mm)

    def handle_spawn(self, mm):
        if mm.nZombieWaves in [1, 10]:
            self.wave1_10(mm)
        elif mm.nZombieWaves in [2, 11]:
            self.wave2_11(mm)
        elif mm.nZombieWaves in range(3, 9) or mm.nZombieWaves in range(12, 19):
            self.regular_wave(mm)
        elif mm.nZombieWaves in [9, 19]:
            self.wave9_19(mm)
        elif mm.nZombieWaves == 20:
            self.wave20(mm)

    def wave1_10(self, mm):
        self.select_specific_operation(4, mm)

    def wave2_11(self, mm):
        if mm.nZombieWaves == 2 and self.spawnHandler[0] == GigaStrategy.cherry_and_jalapeno_front or\
                mm.nZombieWaves == 11 and self.spawnHandler[-1] == GigaStrategy.cherry_and_jalapeno_front:

            self.select_specific_operation(0, mm)
        else:
            self.select_regular_operation()

    def regular_wave(self, mm):
        def set_timestamp(cs):
            def l(mm):
                self.lastRegularAttack = mm.timestamp + cs
            return l

        if mm.nZombieWaves in [3, 12]:
            self.squashLauncher.start(mm)

        self.select_regular_operation()

        if self.launcherUsed[-1] == ImitaterDoomLauncher:
            self.launcherUsed[-1].on_finished(set_timestamp(420))
        else:
            self.launcherUsed[-1].on_finished(set_timestamp(100))

    def wave9_19(self, mm):
        print("wave9_19: " + str(mm.nZombieWaves))
        print("wave9_19: Cherry & Jalapeno " + str(CherryAndJalapenoLauncher.time_remain(mm) / 100) + 's')
        print("wave9_19: Doom-Shroom " + str(DoomLauncher.time_remain(mm) / 100) + 's')
        print("wave9_19: Imitater Doom-Shroom " + str(ImitaterDoomLauncher.time_remain(mm) / 100) + 's')
        self.regular_wave(mm)
        self.launcherUsed[-1].on_finished(self.clean_mode)

        mm.set_timeout(2000, lambda mm: self.squashLauncher.stop(mm))

    def wave20(self, mm):
        self.select_specific_operation(4, mm)
        self.launcherUsed[-1].on_finished(self.clean_mode)

    def clean_mode(self, mm):
        def phase1(mm):
            for zombie in mm.zombies:
                if zombie.type in [Zombie.GIGA_GARGANTUAR, Zombie.GARGANTUAR] and zombie.row in [0, 5] and zombie.hp > 2400:
                    self.select_regular_operation()
                    self.launcherUsed[-1].on_finished(phase2)
                    return

        def phase2(mm):
            def fn(mm):
                for zombie in mm.zombies:
                    if zombie.type in [Zombie.GIGA_GARGANTUAR, Zombie.GARGANTUAR] and zombie.hp > 2400 and zombie.row in [0, 5]:
                        print("Need 2th clean: " + str(zombie.hp) + " " + str(zombie.row))
                        self.select_specific_operation(1, mm, False)
                        return

            print(self.launcherUsed[-1])
            if self.launcherUsed[-1] == ImitaterDoomLauncher:
                delay = 430
            else:
                delay = 110

            mm.set_timeout(delay, fn)

        print("Clean mode activate, current wave is: " + str(mm.nZombieWaves))
        print("Clean Mode: Cherry & Jalapeno " + str(CherryAndJalapenoLauncher.time_remain(mm) / 100) + 's')
        print("Clean Mode: Doom-Shroom " + str(DoomLauncher.time_remain(mm) / 100) + 's')
        print("Clean Mode: Imitater Doom-Shroom " + str(ImitaterDoomLauncher.time_remain(mm) / 100) + 's')
        mm.update(False)
        if self.launcherUsed[-1] == ImitaterDoomLauncher:
            mm.set_timeout(430, phase1)
        else:
            mm.set_timeout(110, phase1)
