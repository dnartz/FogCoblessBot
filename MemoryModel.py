import ctypes
from GameUtils import read_game_memory, mouse_left_click, mouse_reset


class Item:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Card:
    def __init__(self, time_remain, plant_type, card_x, imitater_type, usable):
        self.timeRemain = time_remain
        self.type = plant_type
        self.imitaterType = imitater_type
        self.cardX = card_x + 20
        self.cardY = 40
        self.usable = usable


class Crater:
    def __init__(self, row, col, timeout):
        self.row = row
        self.col = col
        self.timeout = timeout


class Plant:
    LILY_PAD = 16
    CHERRY = 2
    JALAPENO = 20
    SQUASH = 17
    SPIKE_WEED = 21
    PUMPKIN = 30
    COFFEE_BEAN = 35
    FUME_SHROOM = 10
    DOOM_SHROOM = 15
    CLOVER = 27
    ICE_SHROOM = 14
    IMITATER = 48

    def __init__(self, row, col, x, y, hp, plant_type):
        self.row = row
        self.col = col
        self.x = x
        self.y = y
        self.hp = hp
        self.type = plant_type


class Zombie:
    FOOTBALL = 7
    BALLOON = 16
    BUNGEE = 20
    DOPHIN = 14
    JACK_IN_THE_BOX = 15
    SNORKEL = 11
    ZOMBONI = 12
    GARGANTUAR = 23
    GIGA_GARGANTUAR = 32

    def __init__(self, x, y, row, hp, zombie_type):
        self.hp = hp
        self.x = x
        self.y = y
        self.type = zombie_type
        self.row = row


from CommonStrategy import *


class MemoryModel:
    ICE_PATH_LIMIT = [108, 188, 268, 348, 428, 508, 588, 668, 751]

    def __init__(self):
        self.nextDoomExplodeAt = None

        self.itemCollector = ItemCollector()
        self.pumpkinFixer = PumpkinFixer()
        self.fumeFixer = FumeFixer()
        self.fodderOperator = FodderOperator()
        self.balloonTracker = BalloonTracker()

        self.memoryObserver = [self.itemCollector, self.pumpkinFixer, self.fumeFixer, self.fodderOperator, self.balloonTracker]
        self.gameStartObserver = []

        self.baseAddr = read_game_memory(ctypes.c_uint32(), 0x6a9ec0) + 0x768
        self.baseAddr = read_game_memory(ctypes.c_uint32(), self.baseAddr)

        self.itemBase = self.read_int32_from_base(0xe4)
        self.gridItemBase = self.read_int32_from_base(0x11c)
        self.cardBase = self.read_int32_from_base(0x144)
        self.plantBase = self.read_int32_from_base(0xac)
        self.zombieBase = self.read_int32_from_base(0x90)

        self.gridStatus = []

        self.sunCount = 0
        self.timestamp = 0
        self.nextSpawn = 0
        self.spawnedAt = 0
        self.nZombies = 0
        self.triggerHp = None

        self.nPlants = 0
        self.plants = []

        self.nItems = 0
        self.items = []

        self.nGridItems = 0
        self.craters = []
        self.icePath = []
        self.icePathCountdown = []

        self.nZombieWaves = 0

        self.cards = {}

        self.zombies = []
        self.minZombieX = [{}, {}, {}, {}, {}, {}]
        self.maxZombieX = [{}, {}, {}, {}, {}, {}]
        self.maxZombieHp = [{}, {}, {}, {}, {}, {}]
        self.hasZombie = {}

        self.optrQueue = []

        self.strategy = None

        self.jackExploding = False

        self.newWave = False

    def read_int32_from_base(self, *addrs):
        return self.read_memory_from_base(ctypes.c_int32(), *addrs)

    def read_memory_from_base(self, datatype, *addrs):
        p = self.baseAddr + addrs[0]
        for addr in addrs[1:-1]:
            p = read_game_memory(ctypes.c_void_p, p) + addr

        return read_game_memory(datatype, p)

    def grow_plant(self, plant_type, row, col, force=False):
        card = self.cards[plant_type]
        if not card or not card.usable:
            return False

        if not self.gridStatus[row][col] and plant_type != Plant.PUMPKIN:
            if force:
                mouse_reset()
                mouse_left_click(638, 41)
                mouse_left_click(80 + 80 * col, 130 + 85 * row)
            else:
                return False

        mouse_reset()
        mouse_left_click(card.cardX, card.cardY)
        mouse_left_click(80 + 80 * col, 130 + 85 * row)

        card.usable = False
        if card.type not in [Plant.PUMPKIN, Plant.LILY_PAD]:
            self.gridStatus[row][col] = False

        return True

    def update(self, send_event=True):
        self.gridStatus = [[True for j in range(0, 9)] for i in range(0, 6)]

        self.sunCount = self.read_int32_from_base(0x5560)
        self.triggerHp = self.read_int32_from_base(0x5594)

        self.nextSpawn = self.read_int32_from_base(0x559c)

        current_wave = self.read_int32_from_base(0x557c)
        self.newWave = current_wave != self.nZombieWaves
        self.nZombieWaves = current_wave

        self.timestamp = self.read_int32_from_base(0x5568)
        if self.nextDoomExplodeAt is not None and self.timestamp > self.nextDoomExplodeAt:
            self.nextDoomExplodeAt = None

        if self.newWave:
            self.spawnedAt = self.timestamp

        self.update_crater_info()
        self.update_ice_path_info()
        self.update_item_info()
        self.update_plant_info()
        self.update_zombie_info()
        self.update_card_info()

        if send_event:
            if self.newWave:
                self.strategy.handle_spawn(self)

            while len(self.optrQueue) > 0 and self.optrQueue[0][0] <= self.timestamp:
                self.optrQueue[0][1](self)
                self.optrQueue = self.optrQueue[1:]

            for ob in self.memoryObserver:
                ob.update(self)

    def update_crater_info(self):
        self.craters = []
        self.nGridItems = self.read_int32_from_base(0x12c)

        for i in range(0, read_game_memory(ctypes.c_int32(), self.baseAddr + 0x120)):
            item_type = read_game_memory(ctypes.c_int32(), self.gridItemBase + 0x8 + 0xec * i)
            if item_type != 2:
                continue

            disappeared = read_game_memory(ctypes.c_int32(), self.gridItemBase + 0x20 + 0xec * i)
            if disappeared != 0:
                continue

            row = read_game_memory(ctypes.c_int32(), self.gridItemBase + 0x14 + 0xec * i)
            col = read_game_memory(ctypes.c_int32(), self.gridItemBase + 0x10 + 0xec * i)
            timeout = read_game_memory(ctypes.c_int32(), self.gridItemBase + 0x18 + 0xec * i)
            if row not in range(0, 6) or col not in range(0, 9) or timeout not in range(1, 18001):
                continue

            self.craters.append(Crater(row, col, timeout))

            last = self.craters[-1]
            self.gridStatus[last.row][last.col] = False

    def update_ice_path_info(self):
        self.icePath = [0 for i in range(0, 6)]
        self.icePathCountdown = [0 for i in range(0, 6)]

        for i in [0, 1, 4, 5]:
            self.icePath[i] = self.read_memory_from_base(ctypes.c_int32(), 0x60c + 4 * i)
            self.icePathCountdown[i] = self.read_memory_from_base(ctypes.c_int32(), 0x624 + 4 * i)
            for col, edge in enumerate(MemoryModel.ICE_PATH_LIMIT):
                if self.icePath[i] < edge:
                    for j in range(col, 9):
                        self.gridStatus[i][j] = False

    def update_item_info(self):
        self.items = []
        self.nItems = self.read_int32_from_base(0xf4)

        for i in range(0, 256):
            try:
                itemx = int(read_game_memory(ctypes.c_float(), self.itemBase + 0x24 + 0xd8 * i))
                itemy = int(read_game_memory(ctypes.c_float(), self.itemBase + 0x28 + 0xd8 * i))
            except:
                continue

            if itemx not in range(1, 801) or itemy not in range(1, 601):
                continue

            picked = read_game_memory(ctypes.c_uint8(), self.itemBase + 0x50 + 0xd8 * i)
            if picked != 0:
                continue

            self.items.append(Item(itemx, itemy))

    def update_plant_info(self):
        self.plants = []
        self.nPlants = self.read_int32_from_base(0xbc)

        for i in range(0, self.read_int32_from_base(0xb0)):
            disappeared = read_game_memory(ctypes.c_uint8(), self.plantBase + 0x141 + 0x14c * i)
            flattened = read_game_memory(ctypes.c_uint8(), self.plantBase + 0x141 + 0x14c * i)
            if disappeared != 0 or flattened != 0:
                continue

            self.plants.append(Plant(
                    x=read_game_memory(ctypes.c_int32(), self.plantBase + 0x8 + 0x14c * i),
                    y=read_game_memory(ctypes.c_int32(), self.plantBase + 0xc + 0x14c * i),
                    row=read_game_memory(ctypes.c_int32(), self.plantBase + 0x1c + 0x14c * i),
                    col=read_game_memory(ctypes.c_int32(), self.plantBase + 0x28 + 0x14c * i),
                    hp=read_game_memory(ctypes.c_int32(), self.plantBase + 0x40 + 0x14c * i),
                    plant_type=read_game_memory(ctypes.c_int32(), self.plantBase + 0x24 + 0x14c * i)
            ))

            last = self.plants[-1]
            self.gridStatus[last.row][last.col] &= last.type in [Plant.PUMPKIN, Plant.LILY_PAD]

    def update_zombie_info(self):
        self.zombies = []
        self.jackExploding = False

        for i in range(0, 33):
            self.hasZombie[i] = False

        for row in range(0, 6):
            for zombie_type in range(0, 33):
                self.minZombieX[row][zombie_type] = None
                self.maxZombieX[row][zombie_type] = None
                self.maxZombieHp[row][zombie_type] = None

        for i in range(0, self.read_int32_from_base(0x94)):
            disappeared = read_game_memory(ctypes.c_uint8(), self.zombieBase + 0xec + 0x15c * i)
            living = read_game_memory(ctypes.c_uint8(), self.zombieBase + 0xba + 0x15c * i)

            hp = read_game_memory(ctypes.c_int32(), self.zombieBase + 0xc8 + 0x15c * i)

            status = read_game_memory(ctypes.c_int32(), self.zombieBase + 0x28 + 0x15c * i)
            if status in [1, 2, 3] or read_game_memory(ctypes.c_uint8(), self.zombieBase + 0x24 + 0x15c * i) in [9, 20, 24]:
                continue

            zombie_type = read_game_memory(ctypes.c_uint8(), self.zombieBase + 0x24 + 0x15c * i)
            if zombie_type not in range(0, 33):
                continue

            row = read_game_memory(ctypes.c_uint8(), self.zombieBase + 0x1c + 0x15c * i)
            if row not in range(0, 6):
                continue

            if disappeared != 0 or hp < 1 or not living:
                continue

            zombie = Zombie(
                    hp=hp,
                    x=read_game_memory(ctypes.c_float(), self.zombieBase + 0x2c + 0x15c * i),
                    y=read_game_memory(ctypes.c_float(), self.zombieBase + 0x30 + 0x15c * i),
                    row=row,
                    zombie_type=zombie_type
            )
            self.zombies.append(zombie)

            if self.minZombieX[zombie.row][zombie.type] is None:
                self.minZombieX[zombie.row][zombie.type] = zombie.x
            elif self.minZombieX[zombie.row][zombie.type] > zombie.x:
                self.minZombieX[zombie.row][zombie.type] = zombie.x

            if self.maxZombieX[zombie.row][zombie.type] is None:
                self.maxZombieX[zombie.row][zombie.type] = zombie.x
            elif self.maxZombieX[zombie.row][zombie.type] < zombie.x:
                self.maxZombieX[zombie.row][zombie.type] = zombie.x

            if self.maxZombieHp[zombie.row][zombie.type] is None:
                self.maxZombieHp[zombie.row][zombie.type] = zombie.hp
            elif self.maxZombieHp[zombie.row][zombie.type] < zombie.hp:
                self.maxZombieHp[zombie.row][zombie.type] = zombie.hp

            zombie_status = read_game_memory(ctypes.c_float(), self.zombieBase + 0x60 + 0x15c * i)
            if zombie_status < 100:
                self.hasZombie[zombie.type] = True

            if zombie.type == Zombie.JACK_IN_THE_BOX and zombie_status == 16:
                self.jackExploding = True

    def update_card_info(self):
        self.cards = {}
        for i in range(0, 10):
            imitater_type = None
            plant_type = read_game_memory(ctypes.c_int32(), self.cardBase + 0x5c + 0x50 * i)
            if plant_type == Plant.IMITATER:
                imitater_type = read_game_memory(ctypes.c_int32(), self.cardBase + 0x60 + 0x50 * i)

            self.cards[plant_type] = Card(
                    plant_type=plant_type,
                    imitater_type=imitater_type,
                    card_x=read_game_memory(ctypes.c_int32(), self.cardBase + 0x30 + 0x50 * i),
                    time_remain=read_game_memory(ctypes.c_int32(), self.cardBase + 0x50 + 0x50 * i) -
                                read_game_memory(ctypes.c_int32(), self.cardBase + 0x4c + 0x50 * i),
                    usable=read_game_memory(ctypes.c_uint8(), self.cardBase + 0x70 + 0x50 * i) != 0
            )

    def loop_start(self):
        self.update(False)

        while True:
            self.update()

    def set_timeout(self, timeout, action):
        self.timestamp = self.read_int32_from_base(0x5568)
        self.optrQueue.append((self.timestamp + timeout, action))

        self.optrQueue.sort(key=lambda x: x[0])

    _instance = None

    @staticmethod
    def get_instance():
        if MemoryModel._instance is None:
            MemoryModel._instance = MemoryModel()

        return MemoryModel._instance
