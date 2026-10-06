import win32api
from PIL import ImageGrab

monitors = win32api.EnumDisplayMonitors()
print(f"Total active monitors: {len(monitors)}")
for i, m in enumerate(monitors):
    info = win32api.GetMonitorInfo(m[0])
    rect = info['Monitor']
    print(f"Monitor {i}: {rect}")
    try:
        shot = ImageGrab.grab(bbox=rect, all_screens=True)
        print(f"  Grabbed Monitor {i} successfully! Size: {shot.size}")
    except Exception as e:
        print(f"  Failed grabbing Monitor {i}: {e}")

try:
    all_shot = ImageGrab.grab(all_screens=True)
    print(f"All screens combined grab size: {all_shot.size}")
except Exception as e:
    print(f"Failed all_screens grab: {e}")
