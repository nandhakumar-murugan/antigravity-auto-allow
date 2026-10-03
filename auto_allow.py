"""
Antigravity Auto-Allow Companion (Background Stealth Edition)
Version: 1.2.0

Features:
- Target-Locked: ONLY triggers on Antigravity windows (never affects Chrome, browsers, or other apps)
- Zero-Disruption: Runs quietly in background, instantly restores your mouse cursor and active browser window
- Loud Audible Chime: Dual-tone high-alert chime on every approval so you know it worked while multitasking
- Versioning & Metadata: Full semantic versioning display and release notes
"""

__version__ = "1.2.0"
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

# Configure pyautogui safety
pyautogui.PAUSE = 0.02
pyautogui.FAILSAFE = True

user32 = ctypes.windll.user32

class AutoAllowApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{__app_name__} v{__version__}")
        self.root.geometry("360x305")
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
        self.delay_var = tk.DoubleVar(value=0.35)

        # Dragging variables
        self._drag_start_x = 0
        self._drag_start_y = 0

        self.setup_ui()
        self.position_window()
        self.start_hotkey_listener()

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
        self.status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_dot = tk.Label(self.status_frame, text="●", fg="#72767d", bg="#2b2d31", font=("Segoe UI", 12))
        self.status_dot.pack(side=tk.LEFT, padx=(4, 6))

        self.status_text = tk.Label(
            self.status_frame,
            text="Status: PAUSED (Press F9 to Toggle)",
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
        self.btn_toggle.pack(fill=tk.X, pady=(0, 10))

        # Mode Selection
        mode_frame = tk.Frame(body, bg="#1e1f22")
        mode_frame.pack(fill=tk.X, pady=(0, 6))

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

        # Background Stealth & Target info row
        stealth_frame = tk.Frame(body, bg="#1e1f22")
        stealth_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Checkbutton(
            stealth_frame,
            text="Zero-Disruption (Restore Mouse & App)",
            variable=self.stealth_enabled,
            bg="#1e1f22",
            fg="#949ba4",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # Sound & Test Row
        snd_frame = tk.Frame(body, bg="#1e1f22")
        snd_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Checkbutton(
            snd_frame,
            text="Loud Chime on Click 🔊",
            variable=self.sound_enabled,
            bg="#1e1f22",
            fg="#949ba4",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        btn_test_snd = tk.Button(
            snd_frame,
            text="Test Sound",
            bg="#2b2d31",
            fg="#00a8fc",
            activebackground="#3e4247",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8),
            padx=6,
            command=self.play_chime
        )
        btn_test_snd.pack(side=tk.RIGHT)

        # Stats & Target Lock Footer
        footer_frame = tk.Frame(body, bg="#1e1f22")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        lbl_target = tk.Label(
            footer_frame,
            text=f"🔒 Antigravity Only • v{__version__}",
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
        win_w, win_h = 360, 305
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
        self.status_text.configure(text="Status: ACTIVE (Auto-Clicking ON)", fg="#23a55a")

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
        self.status_text.configure(text="Status: PAUSED (Press F9 to Toggle)", fg="#b9bbbe")

    def play_chime(self):
        """Plays a loud, crisp, pleasant two-tone alert chime."""
        def sound_worker():
            try:
                winsound.Beep(1300, 110)
                winsound.Beep(1850, 160)
            except Exception:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        threading.Thread(target=sound_worker, daemon=True).start()

    def is_antigravity_window(self, x, y):
        """
        Verifies that the window under (x, y) belongs STRICTLY to Antigravity.
        Prevents false clicks in Chrome, Firefox, VS Code, or any other application.
        """
        try:
            pt = wintypes.POINT(x, y)
            hwnd = user32.WindowFromPoint(pt)
            if not hwnd:
                return False, None

            # Get root top-level window
            root_hwnd = user32.GetAncestor(hwnd, 2)  # GA_ROOT
            if not root_hwnd:
                root_hwnd = hwnd

            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(root_hwnd, ctypes.byref(pid))
            
            # Check process name
            proc = psutil.Process(pid.value)
            proc_name = proc.name().lower()
            if "antigravity" in proc_name:
                return True, root_hwnd

            # Also check window title as fallback
            length = user32.GetWindowTextLengthW(root_hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(root_hwnd, buff, length + 1)
                if "antigravity" in buff.value.lower():
                    return True, root_hwnd

            return False, None
        except Exception:
            return False, None

    def detection_loop(self):
        """Monitors screen periodically for the Antigravity modal Submit button."""
        while self.is_running:
            try:
                btn_pos = self.find_submit_button_on_screen()
                if btn_pos and self.is_running:
                    cx, cy = btn_pos

                    # 1. VERIFY TARGET: MUST BE ANTIGRAVITY ONLY!
                    is_target, target_hwnd = self.is_antigravity_window(cx, cy)
                    if not is_target:
                        # Not inside Antigravity! Skip immediately to not disrupt other apps
                        time.sleep(0.8)
                        continue

                    # Brief wait for modal stability
                    time.sleep(self.delay_var.get())

                    # Save current user state for Zero-Disruption
                    prev_active_hwnd = user32.GetForegroundWindow()
                    orig_mouse_x, orig_mouse_y = pyautogui.position()

                    # 2. EXECUTE THE CLICK
                    if self.selected_mode.get() == "always_allow":
                        # Click Option 4 row
                        opt4_x = max(10, cx - 240)
                        opt4_y = max(10, cy - 55)
                        pyautogui.click(opt4_x, opt4_y)
                        time.sleep(0.12)

                    # Click Submit button
                    pyautogui.click(cx, cy)
                    self.click_count += 1

                    # 3. ZERO-DISRUPTION RESTORE:
                    # If user is in another app (Chrome, browser, etc.), restore mouse & active window instantly!
                    if self.stealth_enabled.get():
                        # Instantly return cursor to where user was working
                        pyautogui.moveTo(orig_mouse_x, orig_mouse_y)
                        # Restore foreground focus back to the user's browser/app
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

    def find_submit_button_on_screen(self):
        """Captures screen and detects Antigravity's blue Submit button."""
        try:
            screenshot = ImageGrab.grab()
            w, h = screenshot.size

            y_start = int(h * 0.2)
            y_end = int(h * 0.95)

            for y in range(y_start, y_end, 5):
                streak = 0
                start_x = 0
                for x in range(50, w - 50, 4):
                    r, g, b = screenshot.getpixel((x, y))[:3]
                    # Blue Submit button colors: R < 75, G: 85-175, B: 170-255, (B - R > 100)
                    if r < 75 and 85 <= g <= 175 and 170 <= b <= 255 and (b - r > 100):
                        if streak == 0:
                            start_x = x
                        streak += 4
                    else:
                        if 36 <= streak <= 180:
                            cx = start_x + streak // 2
                            cy = y

                            # Verify vertical thickness
                            h_count = 0
                            for check_y in range(max(0, cy - 25), min(h, cy + 25), 2):
                                pr, pg, pb = screenshot.getpixel((cx, check_y))[:3]
                                if pr < 75 and 85 <= pg <= 175 and 170 <= pb <= 255:
                                    h_count += 2

                            if 15 <= h_count <= 55:
                                # Check dark modal dialog background to the left
                                dark_matches = 0
                                for check_x in range(max(0, cx - 200), cx - 50, 15):
                                    dr, dg, db = screenshot.getpixel((check_x, cy))[:3]
                                    if dr < 55 and dg < 55 and db < 65:
                                        dark_matches += 1

                                if dark_matches >= 4:
                                    return (cx, cy)
                        streak = 0
            return None
        except Exception:
            return None

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
