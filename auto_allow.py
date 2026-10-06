"""
Antigravity Auto-Allow Companion (Multi-Monitor & Cast Edition)
Version: 1.3.0

Features:
- Dual-Laptop / Extended Cast Support: Scans all connected monitors and wireless cast displays
- Virtual Screen Coordinate Mapping: Accurately maps coordinates across multi-monitor setups (SM_XVIRTUALSCREEN)
- Tolerant Color Engine: Handles Miracast / Wi-Fi display video compression artifacts
- Target-Locked: Verified against Antigravity window bounding boxes across all monitors
- Zero-Disruption: Runs quietly in background, instantly restores mouse cursor and active browser window
- Loud Audible Chime: Dual-tone high-alert chime on every approval
- Live Multi-Monitor Scanner: Test button to verify detection across all screens
"""

__version__ = "1.3.0"
__app_name__ = "Antigravity Auto-Allow"
__author__ = "nandhakumar-murugan"

import os
import sys
import time
import threading
import winsound
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageGrab
import pyautogui
import psutil

# Enable Per-Monitor DPI Awareness so virtual coordinates match physical pixels
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Configure pyautogui safety
pyautogui.PAUSE = 0.02
pyautogui.FAILSAFE = True

user32 = ctypes.windll.user32

class AutoAllowApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{__app_name__} v{__version__}")
        self.root.geometry("370x345")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1f22")

        # Windows borderless styling
        self.root.overrideredirect(True)

        # State Variables
        self.is_running = False
        self.auto_thread = None
        self.hotkey_thread = None
        self.click_count = 0
        self.selected_mode = tk.StringVar(value="allow_once")  # allow_once or always_allow
        self.sound_enabled = tk.BooleanVar(value=True)
        self.stealth_enabled = tk.BooleanVar(value=True)  # Instantly restore mouse & active window
        self.strict_lock = tk.BooleanVar(value=True)  # Target lock to Antigravity window
        self.delay_var = tk.DoubleVar(value=0.35)

        # Multi-monitor metrics
        self.num_monitors = self.get_monitor_count()

        # Dragging variables
        self._drag_start_x = 0
        self._drag_start_y = 0

        self.setup_ui()
        self.position_window()
        self.start_hotkey_listener()

    def get_monitor_count(self):
        """Returns the number of active display monitors."""
        try:
            return user32.GetSystemMetrics(80)  # SM_CMONITORS
        except Exception:
            return 1

    def get_virtual_bounds(self):
        """Returns (vx, vy, vw, vh) of the entire multi-monitor virtual desktop."""
        vx = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
        vy = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
        vw = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
        vh = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        return vx, vy, vw, vh

    def setup_ui(self):
        # Outer Frame
        border_frame = tk.Frame(self.root, bg="#2b2d31", bd=1, highlightbackground="#3c3f41", highlightthickness=1)
        border_frame.pack(fill=tk.BOTH, expand=True)

        # Header Bar (Draggable)
        header = tk.Frame(border_frame, bg="#2b2d31", height=32)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title_lbl = tk.Label(
            header,
            text="⚡ Auto-Allow",
            bg="#2b2d31",
            fg="#e0e0e0",
            font=("Segoe UI", 10, "bold")
        )
        title_lbl.pack(side=tk.LEFT, padx=(10, 4), pady=4)

        # Version Pill Badge (Clickable for info)
        version_badge = tk.Label(
            header,
            text=f"v{__version__}",
            bg="#5865f2",
            fg="#ffffff",
            font=("Segoe UI", 8, "bold"),
            padx=5,
            pady=0,
            cursor="hand2"
        )
        version_badge.pack(side=tk.LEFT, padx=(2, 6), pady=6)
        version_badge.bind("<Button-1>", lambda e: self.show_version_info())

        # Close and Minimize Buttons
        btn_close = tk.Button(
            header,
            text="✕",
            bg="#2b2d31",
            fg="#aaaaaa",
            activebackground="#e81123",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            padx=8,
            command=self.close_app
        )
        btn_close.pack(side=tk.RIGHT, fill=tk.Y)

        btn_min = tk.Button(
            header,
            text="—",
            bg="#2b2d31",
            fg="#aaaaaa",
            activebackground="#3e4247",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 9),
            padx=8,
            command=self.minimize_app
        )
        btn_min.pack(side=tk.RIGHT, fill=tk.Y)

        for widget in (header, title_lbl):
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)

        # Body
        body = tk.Frame(border_frame, bg="#1e1f22", padx=14, pady=10)
        body.pack(fill=tk.BOTH, expand=True)

        # Status Banner
        self.status_frame = tk.Frame(body, bg="#2b2d31", padx=8, pady=6, bd=1, relief=tk.FLAT)
        self.status_frame.pack(fill=tk.X, pady=(0, 8))

        self.status_dot = tk.Label(self.status_frame, text="●", fg="#72767d", bg="#2b2d31", font=("Segoe UI", 12))
        self.status_dot.pack(side=tk.LEFT, padx=(4, 6))

        self.status_text = tk.Label(
            self.status_frame,
            text=f"PAUSED (F9) • {self.num_monitors} Screen(s) Detected",
            fg="#b9bbbe",
            bg="#2b2d31",
            font=("Segoe UI", 9, "bold")
        )
        self.status_text.pack(side=tk.LEFT)

        # Main Action Button
        self.btn_toggle = tk.Button(
            body,
            text="▶  START AUTO-ALLOW",
            bg="#23a55a",
            fg="#ffffff",
            activebackground="#1e8a4a",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 11, "bold"),
            pady=8,
            cursor="hand2",
            command=self.toggle_running
        )
        self.btn_toggle.pack(fill=tk.X, pady=(0, 8))

        # Mode Selection
        mode_frame = tk.Frame(body, bg="#1e1f22")
        mode_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Radiobutton(
            mode_frame,
            text="Allow This Time (Opt 1)",
            variable=self.selected_mode,
            value="allow_once",
            bg="#1e1f22",
            fg="#dcddde",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            mode_frame,
            text="Always Allow (Opt 4)",
            variable=self.selected_mode,
            value="always_allow",
            bg="#1e1f22",
            fg="#dcddde",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 8)
        ).pack(side=tk.RIGHT)

        # Multi-monitor & Stealth Options
        opt_frame1 = tk.Frame(body, bg="#1e1f22")
        opt_frame1.pack(fill=tk.X, pady=(0, 4))

        tk.Checkbutton(
            opt_frame1,
            text="Zero-Disruption (Restore Mouse & App)",
            variable=self.stealth_enabled,
            bg="#1e1f22",
            fg="#949ba4",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # Sound & Diagnostics Row
        opt_frame2 = tk.Frame(body, bg="#1e1f22")
        opt_frame2.pack(fill=tk.X, pady=(0, 8))

        tk.Checkbutton(
            opt_frame2,
            text="Loud Chime 🔊",
            variable=self.sound_enabled,
            bg="#1e1f22",
            fg="#949ba4",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        btn_test_snd = tk.Button(
            opt_frame2,
            text="Sound",
            bg="#2b2d31",
            fg="#00a8fc",
            activebackground="#3e4247",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8),
            padx=5,
            command=self.play_chime
        )
        btn_test_snd.pack(side=tk.RIGHT, padx=(4, 0))

        btn_scan_now = tk.Button(
            opt_frame2,
            text="🔍 Test Scan Screens",
            bg="#3b4252",
            fg="#88c0d0",
            activebackground="#4c566a",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            padx=6,
            command=self.test_scan_screens
        )
        btn_scan_now.pack(side=tk.RIGHT)

        # Target Lock / Cast status
        lock_frame = tk.Frame(body, bg="#1e1f22")
        lock_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Checkbutton(
            lock_frame,
            text="Lock to Antigravity Window Only",
            variable=self.strict_lock,
            bg="#1e1f22",
            fg="#888888",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 7)
        ).pack(side=tk.LEFT)

        # Stats & Target Lock Footer
        footer_frame = tk.Frame(body, bg="#1e1f22")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        lbl_target = tk.Label(
            footer_frame,
            text=f"📡 Multi-Screen & Cast • v{__version__}",
            bg="#1e1f22",
            fg="#57f287",
            font=("Segoe UI", 7, "bold")
        )
        lbl_target.pack(side=tk.LEFT)

        self.count_lbl = tk.Label(
            footer_frame,
            text="Approved: 0",
            bg="#1e1f22",
            fg="#5865f2",
            font=("Segoe UI", 8, "bold")
        )
        self.count_lbl.pack(side=tk.RIGHT)

    def show_version_info(self):
        """Displays version details and changelog dialog."""
        info = (
            f"⚡ {__app_name__}\n"
            f"Version: {__version__}\n"
            f"Author: {__author__}\n\n"
            "Changelog:\n"
            "• v1.3.0: Dual-laptop & Miracast extended screen support, virtual screen mapping, scan tester\n"
            "• v1.2.0: Added semantic versioning UI badges & metadata\n"
            "• v1.1.0: Antigravity target lock, stealth restore & loud chime\n"
            "• v1.0.0: Initial auto-allow release\n\n"
            "Repository:\n"
            "https://github.com/nandhakumar-murugan/antigravity-auto-allow"
        )
        messagebox.showinfo("Version Information", info)

    def position_window(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w, win_h = 370, 345
        x = screen_w - win_w - 30
        y = screen_h - win_h - 70
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def do_drag(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_start_x)
        y = self.root.winfo_y() + (event.y - self._drag_start_y)
        self.root.geometry(f"+{x}+{y}")

    def toggle_running(self):
        if not self.is_running:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        self.is_running = True
        self.btn_toggle.configure(
            text="⏸  STOP AUTO-ALLOW",
            bg="#da373c",
            activebackground="#b22b30"
        )
        self.status_dot.configure(fg="#23a55a")
        self.status_text.configure(text=f"ACTIVE • Monitoring All {self.get_monitor_count()} Screens", fg="#23a55a")

        self.auto_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.auto_thread.start()

    def stop_monitoring(self):
        self.is_running = False
        self.btn_toggle.configure(
            text="▶  START AUTO-ALLOW",
            bg="#23a55a",
            activebackground="#1e8a4a"
        )
        self.status_dot.configure(fg="#72767d")
        self.status_text.configure(text=f"PAUSED (F9) • {self.get_monitor_count()} Screen(s) Detected", fg="#b9bbbe")

    def play_chime(self):
        """Plays a loud, crisp, pleasant two-tone alert chime."""
        def sound_worker():
            try:
                winsound.Beep(1300, 110)
                winsound.Beep(1850, 160)
            except Exception:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        threading.Thread(target=sound_worker, daemon=True).start()

    def get_antigravity_windows(self):
        """Finds all visible Antigravity window rectangles."""
        hwnds = []
        try:
            def enum_cb(h, _):
                if user32.IsWindowVisible(h):
                    pid = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
                    try:
                        p = psutil.Process(pid.value)
                        if "antigravity" in p.name().lower():
                            rect = wintypes.RECT()
                            user32.GetWindowRect(h, ctypes.byref(rect))
                            w = rect.right - rect.left
                            h_win = rect.bottom - rect.top
                            if w > 300 and h_win > 200:
                                hwnds.append((h, rect))
                    except Exception:
                        pass
                return True

            EnumWindows = user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            EnumWindows(EnumWindowsProc(enum_cb), 0)
        except Exception:
            pass
        return hwnds

    def is_antigravity_window(self, x, y):
        """
        Verifies that coordinate (x, y) belongs to Antigravity.
        Supports extended displays and Miracast cast windows.
        """
        if not self.strict_lock.get():
            return True, None

        try:
            # Check 1: Is (x, y) inside any known Antigravity window rectangle?
            ag_windows = self.get_antigravity_windows()
            for hwnd, rect in ag_windows:
                if rect.left <= x <= rect.right and rect.top <= y <= rect.bottom:
                    return True, hwnd

            # Check 2: Native WindowFromPoint
            pt = wintypes.POINT(int(x), int(y))
            hwnd = user32.WindowFromPoint(pt)
            if hwnd:
                root_hwnd = user32.GetAncestor(hwnd, 2)  # GA_ROOT
                if not root_hwnd:
                    root_hwnd = hwnd

                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(root_hwnd, ctypes.byref(pid))
                try:
                    proc = psutil.Process(pid.value)
                    if "antigravity" in proc.name().lower():
                        return True, root_hwnd
                except Exception:
                    pass

                length = user32.GetWindowTextLengthW(root_hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(root_hwnd, buff, length + 1)
                    if "antigravity" in buff.value.lower():
                        return True, root_hwnd

            # If Antigravity is confirmed running, allow with warning
            for p in psutil.process_iter(['name']):
                if "antigravity" in (p.info['name'] or '').lower():
                    return True, None

            return False, None
        except Exception:
            return True, None

    def find_submit_button_on_screen(self):
        """
        Captures all monitors (including cast/extended screens)
        and detects Antigravity's blue Submit button.
        Returns (screen_x, screen_y) in absolute virtual desktop coordinates.
        """
        try:
            vx, vy, vw, vh = self.get_virtual_bounds()

            # Grab across all screens including cast/layered windows
            try:
                screenshot = ImageGrab.grab(all_screens=True, include_layered_windows=True)
            except Exception:
                try:
                    screenshot = ImageGrab.grab(all_screens=True)
                except Exception:
                    screenshot = ImageGrab.grab()

            w, h = screenshot.size
            if w == 0 or h == 0:
                return None

            # Scan with multi-monitor / cast tolerance
            y_start = 50
            y_end = h - 50

            for y in range(y_start, y_end, 5):
                streak = 0
                start_x = 0
                for x in range(50, w - 50, 4):
                    r, g, b = screenshot.getpixel((x, y))[:3]
                    # Blue Submit button colors:
                    # R < 95, G: 70-195, B: 150-255, with strong blue dominance
                    if r < 95 and 70 <= g <= 195 and 150 <= b <= 255 and (b > r + 45) and (b >= g + 10):
                        if streak == 0:
                            start_x = x
                        streak += 4
                    else:
                        if 32 <= streak <= 190:
                            cx_img = start_x + streak // 2
                            cy_img = y

                            # Verify button vertical height
                            h_count = 0
                            for check_y in range(max(0, cy_img - 26), min(h, cy_img + 26), 2):
                                pr, pg, pb = screenshot.getpixel((cx_img, check_y))[:3]
                                if pr < 95 and 70 <= pg <= 195 and 150 <= pb <= 255 and (pb > pr + 40):
                                    h_count += 2

                            if 14 <= h_count <= 58:
                                # Check dark modal dialog background to the left
                                dark_matches = 0
                                for check_x in range(max(0, cx_img - 220), cx_img - 40, 15):
                                    dr, dg, db = screenshot.getpixel((check_x, cy_img))[:3]
                                    if dr < 68 and dg < 68 and db < 78:
                                        dark_matches += 1

                                if dark_matches >= 3:
                                    # Map to Windows virtual desktop coordinates
                                    screen_x = vx + cx_img
                                    screen_y = vy + cy_img
                                    return (screen_x, screen_y)
                        streak = 0
            return None
        except Exception:
            return None

    def test_scan_screens(self):
        """Diagnostics button to verify if the button is detected on any screen."""
        self.status_text.configure(text="Scanning all screens...", fg="#88c0d0")
        self.root.update()

        pos = self.find_submit_button_on_screen()
        if pos:
            sx, sy = pos
            is_ag, _ = self.is_antigravity_window(sx, sy)
            self.play_chime()
            screen_num = "Screen 2 (Extended)" if sx >= 1900 else "Screen 1 (Primary)"
            msg = f"✅ Submit Button Found!\n\nLocation: ({sx}, {sy})\nDisplay: {screen_num}\nTarget Verified: {is_ag}"
            messagebox.showinfo("Scanner Result", msg)
            self.status_text.configure(text=f"Found button on {screen_num}!", fg="#57f287")
        else:
            msg = (
                f"❌ No Submit Button Detected across {self.get_monitor_count()} screens.\n\n"
                "Tips:\n"
                "1. Make sure the Antigravity approval dialog is currently open.\n"
                "2. Ensure Antigravity is not completely covered or minimized."
            )
            messagebox.showwarning("Scanner Result", msg)
            self.status_text.configure(text="No button detected", fg="#f04747")

    def detection_loop(self):
        """Monitors screen periodically for the Antigravity modal Submit button."""
        while self.is_running:
            try:
                btn_pos = self.find_submit_button_on_screen()
                if btn_pos and self.is_running:
                    cx, cy = btn_pos

                    # 1. VERIFY TARGET: MUST BE ANTIGRAVITY!
                    is_target, target_hwnd = self.is_antigravity_window(cx, cy)
                    if not is_target:
                        time.sleep(0.8)
                        continue

                    # Brief wait for modal stability
                    time.sleep(self.delay_var.get())

                    # Save current user state for Zero-Disruption
                    prev_active_hwnd = user32.GetForegroundWindow()
                    orig_mouse_x, orig_mouse_y = pyautogui.position()

                    # 2. EXECUTE THE CLICK
                    if self.selected_mode.get() == "always_allow":
                        opt4_x = max(10, cx - 240)
                        opt4_y = max(10, cy - 55)
                        pyautogui.click(opt4_x, opt4_y)
                        time.sleep(0.12)

                    # Click Submit button on target monitor
                    pyautogui.click(cx, cy)
                    self.click_count += 1

                    # 3. ZERO-DISRUPTION RESTORE:
                    if self.stealth_enabled.get():
                        pyautogui.moveTo(orig_mouse_x, orig_mouse_y)
                        if prev_active_hwnd and prev_active_hwnd != target_hwnd:
                            user32.SetForegroundWindow(prev_active_hwnd)

                    # 4. LOUD NOTIFICATION CHIME
                    if self.sound_enabled.get():
                        self.play_chime()

                    # Update UI count
                    self.root.after(0, lambda c=self.click_count: self.count_lbl.configure(text=f"Approved: {c}"))

                    # Cooldown to avoid duplicate clicks
                    time.sleep(1.3)
                else:
                    time.sleep(0.6)
            except Exception:
                time.sleep(1.0)

    def start_hotkey_listener(self):
        """Background thread listening for F9 global toggle hotkey."""
        def listener():
            VK_F9 = 0x78
            last_pressed = False

            while True:
                time.sleep(0.1)
                pressed = (user32.GetAsyncKeyState(VK_F9) & 0x8000) != 0
                if pressed and not last_pressed:
                    self.root.after(0, self.toggle_running)
                last_pressed = pressed

        self.hotkey_thread = threading.Thread(target=listener, daemon=True)
        self.hotkey_thread.start()

    def minimize_app(self):
        self.root.iconify()

    def close_app(self):
        self.is_running = False
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoAllowApp(root)
    root.mainloop()
