from time import sleep
from GameUtils import open_game_window, mouse_left_click, mouse_move
from MemoryModel import MemoryModel
from GigaStrategy import *
from CommonStrategy import *


def select_card():
    mm = MemoryModel.get_instance()

    mouse_left_click(417, 228)

    mouse_move(489, 538)
    sleep(0.1)
    mouse_left_click(489, 538)
    sleep(0.1)
    mouse_left_click(570, 233)

    for p in [(360, 226),
              (259, 297),
              (40, 295),
              (149, 158),
              (92, 296),
              (206, 363),
              (356, 360),
              (160, 226)]:
        mouse_left_click(*p)

    mouse_move(227, 567)
    mouse_left_click(227, 567)

    # 等待游戏开始
    orign = mm.read_int32_from_base(0x5568)
    while orign == mm.read_int32_from_base(0x5568):
        pass


def main():
    open_game_window()
    mm = MemoryModel.get_instance()

    select_card()

    mm.strategy = GigaStrategy()
    mm.loop_start()

if __name__ == "__main__":
    main()