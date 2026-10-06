"""
Antigravity Auto-Allow Companion (Ultra-Tolerant Multi-Screen Edition)
Version: 1.5.0

Features:
- Ultra-Tolerant Color Matching (no fragile background checks; catches all cast/Miracast blue buttons)
- Live Real-Time Activity Log right inside the widget UI
- Direct Win32 Native Cursor Positioning + Left Click + Enter key fallback
- Manual Instant Approve Hotkey (F8)
- 'Force Click Submit' one-touch diagnostic button
- Zero-Disruption: Instantly restores mouse cursor to where you were working
- Loud Audible Chime on every approval
"""

__version__ = "1.5.0"
__app_name__ = "Antigravity Auto-Allow"
__author__ = "nandhakumar-murugan"

import os
import sys
import time
import datetime
import threading
import winsound
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageGrab
import pyautogui
import psutil
import win32api
import win32con

# Enable Per-Monitor DPI Awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

pyautogui.PAUSE = 0.02
pyautogui.FAILSAFE = True

user32 = ctypes.windll.user32

class AutoAllowApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{__app_name__} v{__version__}")
        self.root.geometry("400x410")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1f22")

        self.root.overrideredirect(True)

        self.is_running = False
        self.auto_thread = None
        self.hotkey_thread = None
        self.click_count = 0
        self.selected_mode = tk.StringVar(value="allow_once")  # allow_once or always_allow
        self.sound_enabled = tk.BooleanVar(value=True)
        self.stealth_enabled = tk.BooleanVar(value=True)
        self.delay_var = tk.DoubleVar(value=0.20)

        self.last_detected_pos = None

        self._drag_start_x = 0
        self._drag_start_y = 0

        self.setup_ui()
        self.position_window()
        self.start_hotkey_listener()

    def get_monitor_count(self):
        try:
            return user32.GetSystemMetrics(80)
        except Exception:
            return 1

    def get_virtual_bounds(self):
        vx = user32.GetSystemMetrics(76)
        vy = user32.GetSystemMetrics(77)
        vw = user32.GetSystemMetrics(78)
        vh = user32.GetSystemMetrics(79)
        return vx, vy, vw, vh

    def log(self, text, color="#b9bbbe"):
        """Logs a timestamped message into the on-screen live log box."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        msg = f"[{now}] {text}"
        try:
            self.log_lbl.configure(text=msg, fg=color)
        except Exception:
            pass

    def setup_ui(self):
        border_frame = tk.Frame(self.root, bg="#2b2d31", bd=1, highlightbackground="#3c3f41", highlightthickness=1)
        border_frame.pack(fill=tk.BOTH, expand=True)

        # Header Bar
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
            text=f"PAUSED (F9) • {self.get_monitor_count()} Displays Active",
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

        # Stealth & Chime Row
        opt_frame1 = tk.Frame(body, bg="#1e1f22")
        opt_frame1.pack(fill=tk.X, pady=(0, 4))

        tk.Checkbutton(
            opt_frame1,
            text="Zero-Disruption (Restore Mouse)",
            variable=self.stealth_enabled,
            bg="#1e1f22",
            fg="#949ba4",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        tk.Checkbutton(
            opt_frame1,
            text="Loud Chime 🔊",
            variable=self.sound_enabled,
            bg="#1e1f22",
            fg="#949ba4",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 8)
        ).pack(side=tk.RIGHT)

        # Diagnostic Action Buttons
        test_frame = tk.Frame(body, bg="#1e1f22")
        test_frame.pack(fill=tk.X, pady=(0, 6))

        btn_scan_now = tk.Button(
            test_frame,
            text="🔍 Find Button",
            bg="#3b4252",
            fg="#88c0d0",
            activebackground="#4c566a",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=4,
            command=self.test_scan_screens
        )
        btn_scan_now.pack(side=tk.LEFT)

        btn_force_click = tk.Button(
            test_frame,
            text="🎯 Force Click Submit",
            bg="#4c566a",
            fg="#ebcb8b",
            activebackground="#5e81ac",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=4,
            command=self.force_click_submit
        )
        btn_force_click.pack(side=tk.LEFT, padx=(6, 0))

        btn_test_snd = tk.Button(
            test_frame,
            text="Chime",
            bg="#2b2d31",
            fg="#00a8fc",
            activebackground="#3e4247",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8),
            padx=6,
            pady=4,
            command=self.play_chime
        )
        btn_test_snd.pack(side=tk.RIGHT)

        # Live Real-time Activity Log Box
        log_box = tk.Frame(body, bg="#141517", padx=8, pady=6, bd=1, relief=tk.SUNKEN)
        log_box.pack(fill=tk.X, pady=(0, 6))

        self.log_lbl = tk.Label(
            log_box,
            text="[Ready] Click '▶ START AUTO-ALLOW' or press F9.",
            bg="#141517",
            fg="#88c0d0",
            font=("Consolas", 8),
            anchor="w",
            justify=tk.LEFT
        )
        self.log_lbl.pack(fill=tk.X)

        # Quick Hotkey Tip
        tip_lbl = tk.Label(
            body,
            text="💡 Shortcuts: F9 = Toggle Auto-Allow | F8 = Instant Approve Now",
            bg="#1e1f22",
            fg="#72767d",
            font=("Segoe UI", 7)
        )
        tip_lbl.pack(fill=tk.X, pady=(0, 4))

        # Footer
        footer_frame = tk.Frame(body, bg="#1e1f22")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        lbl_target = tk.Label(
            footer_frame,
            text=f"📡 Multi-Screen Ultra • v{__version__}",
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
        info = (
            f"⚡ {__app_name__}\n"
            f"Version: {__version__}\n"
            f"Author: {__author__}\n\n"
            "Changelog:\n"
            "• v1.5.0: Ultra-tolerant color engine, live log box, F8 instant hotkey, force click button\n"
            "• v1.4.0: Win32 precision clicking, DPI normalization, Enter fallback\n"
            "• v1.3.0: Dual-laptop extended cast screen support\n"
            "• v1.2.0: Version badges and metadata\n"
            "• v1.1.0: Target lock, stealth mode, loud chime\n\n"
            "Repository:\n"
            "https://github.com/nandhakumar-murugan/antigravity-auto-allow"
        )
        messagebox.showinfo("Version Information", info)

    def position_window(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w, win_h = 400, 410
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
        self.log("Auto-Allow ACTIVE. Monitoring for Submit button...", "#57f287")

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
        self.status_text.configure(text=f"PAUSED (F9) • {self.get_monitor_count()} Displays Active", fg="#b9bbbe")
        self.log("Auto-Allow PAUSED.", "#e5c07b")

    def play_chime(self):
        def sound_worker():
            try:
                winsound.Beep(1300, 110)
                winsound.Beep(1850, 160)
            except Exception:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        threading.Thread(target=sound_worker, daemon=True).start()

    def click_at(self, target_x, target_y):
        """
        Direct hardware cursor click using Win32 API.
        Works across all extended monitors and cast laptops.
        """
        try:
            win32api.SetCursorPos((int(target_x), int(target_y)))
            time.sleep(0.04)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.04)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        except Exception:
            pyautogui.click(target_x, target_y)

    def send_enter_key(self):
        """Sends native Enter (VK_RETURN) keypress."""
        try:
            VK_RETURN = 0x0D
            KEYEVENTF_KEYUP = 0x0002
            user32.keybd_event(VK_RETURN, 0, 0, 0)
            time.sleep(0.03)
            user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)
        except Exception:
            pyautogui.press('enter')

    def find_submit_button_on_screen(self):
        """
        Ultra-tolerant screen scanner for the blue Submit button.
        Scans all connected screens without fragile background checks.
        """
        try:
            vx, vy, vw, vh = self.get_virtual_bounds()

            try:
                screenshot = ImageGrab.grab(all_screens=True, include_layered_windows=True)
            except Exception:
                try:
                    screenshot = ImageGrab.grab(all_screens=True)
                except Exception:
                    screenshot = ImageGrab.grab()

            img_w, img_h = screenshot.size
            if img_w == 0 or img_h == 0:
                return None

            scale_x = vw / img_w if img_w else 1.0
            scale_y = vh / img_h if img_h else 1.0

            # Scan rows across all screens
            for y in range(30, img_h - 30, 4):
                streak = 0
                start_x = 0
                for x in range(30, img_w - 30, 3):
                    r, g, b = screenshot.getpixel((x, y))[:3]
                    # Blue button detection:
                    # Blue is distinctly higher than red and green
                    # Covers standard Antigravity blue #007acc as well as cast compressed hues
                    if (b >= 140) and (b > r + 35) and (b > g + 10) and (r < 120):
                        if streak == 0:
                            start_x = x
                        streak += 3
                    else:
                        if 24 <= streak <= 220:
                            cx_img = start_x + streak // 2
                            cy_img = y

                            # Verify button vertical height (thickness)
                            h_count = 0
                            for check_y in range(max(0, cy_img - 25), min(img_h, cy_img + 25), 2):
                                pr, pg, pb = screenshot.getpixel((cx_img, check_y))[:3]
                                if (pb >= 140) and (pb > pr + 30) and (pr < 120):
                                    h_count += 2

                            # Valid button thickness is usually 14 to 55px
                            if 12 <= h_count <= 60:
                                screen_x = vx + int(cx_img * scale_x)
                                screen_y = vy + int(cy_img * scale_y)
                                return (screen_x, screen_y)
                        streak = 0
            return None
        except Exception:
            return None

    def execute_approval(self, cx, cy):
        """Performs the approval click + Enter key + chime + stealth restore."""
        prev_active_hwnd = user32.GetForegroundWindow()
        orig_mouse_x, orig_mouse_y = pyautogui.position()

        # If Option 4 selected, click Option 4 row first
        if self.selected_mode.get() == "always_allow":
            opt4_x = max(10, cx - 220)
            opt4_y = max(10, cy - 50)
            self.click_at(opt4_x, opt4_y)
            time.sleep(0.12)

        # 1. Click the Submit button
        self.click_at(cx, cy)
        time.sleep(0.04)

        # 2. Also send Enter key
        self.send_enter_key()
        self.click_count += 1

        # 3. Stealth restore mouse and window focus
        if self.stealth_enabled.get():
            win32api.SetCursorPos((orig_mouse_x, orig_mouse_y))
            if prev_active_hwnd:
                user32.SetForegroundWindow(prev_active_hwnd)

        # 4. Sound alert
        if self.sound_enabled.get():
            self.play_chime()

        self.root.after(0, lambda c=self.click_count: self.count_lbl.configure(text=f"Approved: {c}"))
        self.root.after(0, lambda: self.log(f"Approved! Clicked at ({cx}, {cy}).", "#57f287"))

    def test_scan_screens(self):
        """Scans screens and reports whether Submit button was found."""
        self.log("Scanning all screens...", "#88c0d0")
        self.root.update()

        pos = self.find_submit_button_on_screen()
        if pos:
            self.last_detected_pos = pos
            sx, sy = pos
            self.play_chime()
            screen_name = "Screen 2 (Extended Cast)" if sx >= 1536 else "Screen 1 (Primary)"
            self.log(f"Found button at ({sx}, {sy}) on {screen_name}!", "#57f287")
            messagebox.showinfo("Scanner Result", f"✅ Submit button detected!\n\nCoordinates: ({sx}, {sy})\nMonitor: {screen_name}\n\nYou can click '🎯 Force Click Submit' to test-click it now!")
        else:
            self.log("Scan complete: No Submit button visible.", "#f04747")
            messagebox.showwarning("Scanner Result", "❌ No Submit button detected on either screen.\n\nMake sure an Antigravity approval dialog is currently open.")

    def force_click_submit(self):
        """Immediately clicks the detected button or sends Enter key."""
        pos = self.find_submit_button_on_screen()
        if pos:
            sx, sy = pos
            self.execute_approval(sx, sy)
            messagebox.showinfo("Clicked", f"🎯 Successfully clicked Submit at ({sx}, {sy})!")
        else:
            # Fallback: send Enter key directly
            self.send_enter_key()
            if self.sound_enabled.get():
                self.play_chime()
            self.log("Sent Enter key directly.", "#ebcb8b")
            messagebox.showinfo("Enter Sent", "Sent Enter key directly to submit focused dialog!")

    def detection_loop(self):
        while self.is_running:
            try:
                btn_pos = self.find_submit_button_on_screen()
                if btn_pos and self.is_running:
                    cx, cy = btn_pos
                    self.log(f"Detected Submit button at ({cx}, {cy})! Clicking...", "#88c0d0")
                    time.sleep(self.delay_var.get())
                    self.execute_approval(cx, cy)
                    time.sleep(1.3)
                else:
                    time.sleep(0.5)
            except Exception as e:
                time.sleep(1.0)

    def start_hotkey_listener(self):
        """Background listener for F9 (toggle) and F8 (instant approve)."""
        def listener():
            VK_F9 = 0x78
            VK_F8 = 0x77
            f9_last = False
            f8_last = False
            while True:
                time.sleep(0.1)
                f9_pressed = (user32.GetAsyncKeyState(VK_F9) & 0x8000) != 0
                if f9_pressed and not f9_last:
                    self.root.after(0, self.toggle_running)
                f9_last = f9_pressed

                f8_pressed = (user32.GetAsyncKeyState(VK_F8) & 0x8000) != 0
                if f8_pressed and not f8_last:
                    self.root.after(0, self.force_click_submit)
                f8_last = f8_pressed

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
