import os
import ctypes
import win32api
import win32con
from PIL import ImageGrab, Image, ImageDraw

user32 = ctypes.windll.user32

vx = user32.GetSystemMetrics(76)
vy = user32.GetSystemMetrics(77)
vw = user32.GetSystemMetrics(78)
vh = user32.GetSystemMetrics(79)

print(f"Virtual Screen Metrics: X={vx}, Y={vy}, W={vw}, H={vh}")

# Grab screenshot
try:
    im = ImageGrab.grab(all_screens=True, include_layered_windows=True)
except Exception:
    im = ImageGrab.grab(all_screens=True)

print(f"Captured Image Size: {im.size}")

# Search for the blue button
w, h = im.size
found_buttons = []

for y in range(20, h - 20, 4):
    streak = 0
    start_x = 0
    for x in range(20, w - 20, 3):
        r, g, b = im.getpixel((x, y))[:3]
        if r < 110 and 70 <= g <= 210 and 150 <= b <= 255 and (b > r + 40) and (b >= g + 8):
            if streak == 0:
                start_x = x
            streak += 3
        else:
            if 25 <= streak <= 240:
                cx = start_x + streak // 2
                cy = y
                # check vertical
                h_count = 0
                for check_y in range(max(0, cy - 25), min(h, cy + 25), 2):
                    pr, pg, pb = im.getpixel((cx, check_y))[:3]
                    if pr < 110 and 70 <= pg <= 210 and 150 <= pb <= 255 and (pb > pr + 35):
                        h_count += 2
                if 12 <= h_count <= 65:
                    found_buttons.append((cx, cy, streak, h_count))
            streak = 0

print(f"Found {len(found_buttons)} candidate button clusters:")
for b in found_buttons[:10]:
    print(f"  Center: ({b[0]}, {b[1]}), Width: ~{b[2]}px, Height: ~{b[3]}px")

# Draw red circles on all candidates and save
draw = ImageDraw.Draw(im)
for b in found_buttons:
    cx, cy = b[0], b[1]
    draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], outline="red", width=4)

debug_path = r"C:\Users\smnk2\.gemini\antigravity\scratch\antigravity_auto_allow\debug_screen.png"
im.save(debug_path)
print(f"Saved debug screenshot with detections to: {debug_path}")
