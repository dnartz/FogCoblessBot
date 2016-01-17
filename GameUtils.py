import ctypes

try:
    import win32con, win32gui, win32ui, win32process, win32api
except ImportError:
    print("挂机程序需要 pywin32 模块。请先安装 pywin32。")
    exit(1)

_PVZ_HWND = 0
_PVZ_WINDOW = None
_PVZ_PROCESS = None


def open_game_window():
    global _PVZ_HWND, _PVZ_PROCESS, _PVZ_WINDOW

    _PVZ_WINDOW = None
    try:
        _PVZ_WINDOW = win32ui.FindWindow(None, "Plants vs. Zombies")
    except:
        try:
            _PVZ_WINDOW = win32ui.FindWindow(None, "植物大战僵尸中文版")
        except:
            print("找不到游戏窗口，请确认你已打开游戏。")
            exit(1)

    hwnd = _PVZ_WINDOW.GetSafeHwnd()
    pid = win32process.GetWindowThreadProcessId(hwnd)[1]

    PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)
    _PVZ_PROCESS = win32api.OpenProcess(PROCESS_ALL_ACCESS, 0, pid)
    _PVZ_HWND = _PVZ_PROCESS.handle

    # 设置后台运行
    # TODO: 1.0版支持
    buffer = ctypes.c_uint8(0xC3)
    ctypes.windll.kernel32.WriteProcessMemory(_PVZ_HWND, 0x00450400, ctypes.byref(buffer), 1)

def read_game_memory(dataType, addr):
    global _PVZ_HWND

    if ctypes.windll.kernel32.ReadProcessMemory(_PVZ_HWND, addr, ctypes.byref(dataType), ctypes.sizeof(dataType), None):
        return dataType.value
    else:
        print(win32api.GetLastError())
        raise MemoryError


def mouse_move(x, y):
    global _PVZ_WINDOW
    _PVZ_WINDOW.SendMessage(win32con.WM_MOUSEMOVE, 0, (y << 16) | x)


def mouse_left_click(x, y):
    global _PVZ_WINDOW
    _PVZ_WINDOW.SendMessage(win32con.WM_LBUTTONDOWN, 0, (y << 16) | x)
    _PVZ_WINDOW.SendMessage(win32con.WM_LBUTTONUP, 0, (y << 16) | x)


def mouse_reset():
    global _PVZ_WINDOW
    _PVZ_WINDOW.SendMessage(win32con.WM_RBUTTONDOWN, 0, (1 << 16) | 1)


def key_press():
    pass

