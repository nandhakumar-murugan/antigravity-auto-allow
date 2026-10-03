"""
Antigravity Auto-Allow Companion
A floating overlay tool that automatically clicks 'Allow this time'
when Antigravity prompts for command/file permissions.
"""

import os
import sys
import time
import threading
import winsound
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageGrab
import pyautogui

# Disable pyautogui pause/fail-safe freeze (keep safe in corners if needed)
pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True

class AutoAllowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Auto-Allow")
        self.root.geometry("340x260")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1f22")

        # Windows-specific borderless / title styling
        self.root.overrideredirect(True)

        # Variables
        self.is_running = False
        self.auto_thread = None
        self.hotkey_thread = None
        self.click_count = 0
        self.selected_mode = tk.StringVar(value="allow_once")  # allow_once or always_allow
        self.sound_enabled = tk.BooleanVar(value=True)
        self.delay_var = tk.DoubleVar(value=0.4)  # seconds delay before clicking

        # Dragging variables
        self._drag_start_x = 0
        self._drag_start_y = 0

        self.setup_ui()
        self.position_window()
        self.start_hotkey_listener()

    def setup_ui(self):
        # Outer Border Frame
        border_frame = tk.Frame(self.root, bg="#2b2d31", bd=1, highlightbackground="#3c3f41", highlightthickness=1)
        border_frame.pack(fill=tk.BOTH, expand=True)

        # Header / Title Bar (Draggable)
        header = tk.Frame(border_frame, bg="#2b2d31", height=32)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # Title Label
        title_lbl = tk.Label(
            header,
            text="⚡ Antigravity Auto-Allow",
            bg="#2b2d31",
            fg="#e0e0e0",
            font=("Segoe UI", 10, "bold")
        )
        title_lbl.pack(side=tk.LEFT, padx=10, pady=4)

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

        # Make header draggable
        for widget in (header, title_lbl):
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)

        # Main Body Container
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

        # Big Main Action Button
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

        # Options Row: Mode Selection
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

        # Secondary settings row: Sound & Count
        settings_frame = tk.Frame(body, bg="#1e1f22")
        settings_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Checkbutton(
            settings_frame,
            text="Sound on Click",
            variable=self.sound_enabled,
            bg="#1e1f22",
            fg="#949ba4",
            selectcolor="#2b2d31",
            activebackground="#1e1f22",
            activeforeground="#ffffff",
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        self.count_lbl = tk.Label(
            settings_frame,
            text="Approved: 0",
            bg="#1e1f22",
            fg="#5865f2",
            font=("Segoe UI", 8, "bold")
        )
        self.count_lbl.pack(side=tk.RIGHT)

        # Hint Footer
        footer = tk.Label(
            body,
            text="💡 Tip: Turn ON after approving plan. Auto-clicks Submit.",
            bg="#1e1f22",
            fg="#72767d",
            font=("Segoe UI", 7)
        )
        footer.pack(side=tk.BOTTOM, pady=(4, 0))

    def position_window(self):
        # Position window near bottom right above taskbar
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w, win_h = 340, 260
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

    def detection_loop(self):
        """Monitors screen periodically for the Antigravity modal Submit button."""
        while self.is_running:
            try:
                btn_pos = self.find_submit_button_on_screen()
                if btn_pos and self.is_running:
                    cx, cy = btn_pos
                    
                    # Optional brief delay to let modal render completely
                    time.sleep(self.delay_var.get())

                    # If Option 4 (Always Allow) is selected, click Option 4 first
                    if self.selected_mode.get() == "always_allow":
                        # In the Antigravity modal, Option 4 is roughly ~55px above Submit and 250px left
                        # But clicking item 4 radio / row:
                        opt4_x = max(10, cx - 240)
                        opt4_y = max(10, cy - 55)
                        pyautogui.click(opt4_x, opt4_y)
                        time.sleep(0.15)

                    # Click the Submit button
                    pyautogui.click(cx, cy)
                    self.click_count += 1
                    
                    # Sound notification
                    if self.sound_enabled.get():
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)

                    # Update UI count
                    self.root.after(0, lambda c=self.click_count: self.count_lbl.configure(text=f"Approved: {c}"))
                    
                    # Cool-down to prevent double-clicking same dialog
                    time.sleep(1.2)
                else:
                    time.sleep(0.6)
            except Exception:
                time.sleep(1.0)

    def find_submit_button_on_screen(self):
        """Captures screen and detects Antigravity's blue Submit button."""
        try:
            screenshot = ImageGrab.grab()
            w, h = screenshot.size

            # Scan the screen in vertical steps
            # Dialog usually appears in the lower or middle half of the screen
            y_start = int(h * 0.2)
            y_end = int(h * 0.95)

            for y in range(y_start, y_end, 5):
                streak = 0
                start_x = 0
                for x in range(50, w - 50, 4):
                    r, g, b = screenshot.getpixel((x, y))[:3]
                    # Blue Submit button colors: R < 70, G: 85-175, B: 170-255, (B - R > 100)
                    if r < 75 and 85 <= g <= 175 and 170 <= b <= 255 and (b - r > 100):
                        if streak == 0:
                            start_x = x
                        streak += 4
                    else:
                        if 36 <= streak <= 180:
                            cx = start_x + streak // 2
                            cy = y

                            # Verify vertical button thickness
                            h_count = 0
                            for check_y in range(max(0, cy - 25), min(h, cy + 25), 2):
                                pr, pg, pb = screenshot.getpixel((cx, check_y))[:3]
                                if pr < 75 and 85 <= pg <= 175 and 170 <= pb <= 255:
                                    h_count += 2

                            if 15 <= h_count <= 55:
                                # Verify dark modal dialog background to the left
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
            user32 = ctypes.windll.user32
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
