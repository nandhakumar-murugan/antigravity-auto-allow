import win32gui
import win32ui
import ctypes
from ctypes import wintypes
import psutil
from PIL import Image

def find_antigravity_hwnd():
    user32 = ctypes.windll.user32
    antigravity_hwnds = []

    def enum_cb(hwnd, _):
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                proc = psutil.Process(pid.value)
                if "antigravity" in proc.name().lower():
                    rect = wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    if w > 400 and h > 300:
                        antigravity_hwnds.append((hwnd, (rect.left, rect.top, w, h)))
            except Exception:
                pass
        return True

    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    EnumWindows(EnumWindowsProc(enum_cb), 0)
    return antigravity_hwnds

hwnds = find_antigravity_hwnd()
print("Found HWNDs:", hwnds)
