"""
Antigravity Auto-Allow Companion (Precision Calibration & Multi-Screen Edition)
Version: 1.4.0

Features:
- Dual-Laptop / Extended Cast Support with DPI-Aware Coordinate Normalization
- Win32 MOUSEEVENTF_VIRTUALDESK Precision Clicker (accurate across all multi-monitor DPI scales)
- Dual Action: Native Precision Click + Smart Enter (VK_RETURN) fallback to guarantee 100% submission
- Live Screen Scanner & 'Test Click' verification button
- Zero-Disruption: Runs quietly in background, instantly restores mouse cursor and active window
- Loud Audible Chime: Dual-tone high-alert chime on every approval
"""

__version__ = "1.4.0"
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

# Enable Per-Monitor DPI Awareness
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
        self.root.geometry("380x370")
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
        self.strict_lock = tk.BooleanVar(value=False)  # Allow clicking Submit across screens
        self.delay_var = tk.DoubleVar(value=0.25)
        self.x_offset = tk.IntVar(value=0)  # Micro-tuning offset
        self.y_offset = tk.IntVar(value=0)

        # Last detected coordinates for diagnostic test click
        self.last_detected_pos = None

        # Dragging variables
        self._drag_start_x = 0
        self._drag_start_y = 0

        self.setup_ui()
        self.position_window()
        self.start_hotkey_listener()

    def get_monitor_count(self):
        try:
            return user32.GetSystemMetrics(80)  # SM_CMONITORS
        except Exception:
            return 1

    def get_virtual_bounds(self):
        vx = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
        vy = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
        vw = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
        vh = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        return vx, vy, vw, vh

    def setup_ui(self):
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

        # Test Diagnostics Row
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
            pady=3,
            command=self.test_scan_screens
        )
        btn_scan_now.pack(side=tk.LEFT)

        btn_test_click = tk.Button(
            test_frame,
            text="🎯 Click Detected Pos",
            bg="#434c5e",
            fg="#ebcb8b",
            activebackground="#4c566a",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=3,
            command=self.test_click_detected
        )
        btn_test_click.pack(side=tk.LEFT, padx=(6, 0))

        btn_test_snd = tk.Button(
            test_frame,
            text="Sound",
            bg="#2b2d31",
            fg="#00a8fc",
            activebackground="#3e4247",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8),
            padx=6,
            pady=3,
            command=self.play_chime
        )
        btn_test_snd.pack(side=tk.RIGHT)

        # Coordinate Info Display
        self.coord_lbl = tk.Label(
            body,
            text="Ready. Click 'Find Button' while modal is open to test.",
            bg="#1e1f22",
            fg="#72767d",
            font=("Segoe UI", 7)
        )
        self.coord_lbl.pack(fill=tk.X, pady=(0, 4))

        # Stats & Target Lock Footer
        footer_frame = tk.Frame(body, bg="#1e1f22")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        lbl_target = tk.Label(
            footer_frame,
            text=f"🎯 Dual Precision • v{__version__}",
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
            "• v1.4.0: Precision Win32 virtual mouse clicks, DPI scaling normalization, dual Enter key fallback\n"
            "• v1.3.0: Dual-laptop & Miracast extended screen support\n"
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
        win_w, win_h = 380, 370
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
        self.status_text.configure(text=f"PAUSED (F9) • {self.get_monitor_count()} Displays Active", fg="#b9bbbe")

    def play_chime(self):
        def sound_worker():
            try:
                winsound.Beep(1300, 110)
                winsound.Beep(1850, 160)
            except Exception:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        threading.Thread(target=sound_worker, daemon=True).start()

    def click_virtual_desktop(self, target_x, target_y):
        """
        Uses Win32 MOUSEEVENTF_VIRTUALDESK to deliver a single-pixel
        accurate click across multi-monitor and mixed-DPI virtual desktops.
        """
        try:
            vx, vy, vw, vh = self.get_virtual_bounds()
            if vw == 0 or vh == 0:
                vw, vh = 1920, 1080

            # Normalize to 0..65535 across virtual desktop
            norm_x = int((target_x - vx) * 65535 / vw)
            norm_y = int((target_y - vy) * 65535 / vh)

            MOUSEEVENTF_MOVE = 0x0001
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_ABSOLUTE = 0x8000
            MOUSEEVENTF_VIRTUALDESK = 0x4000

            flags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
            user32.mouse_event(flags, norm_x, norm_y, 0, 0)
            time.sleep(0.04)
            user32.mouse_event(flags | MOUSEEVENTF_LEFTDOWN, norm_x, norm_y, 0, 0)
            time.sleep(0.04)
            user32.mouse_event(flags | MOUSEEVENTF_LEFTUP, norm_x, norm_y, 0, 0)
        except Exception:
            pyautogui.click(target_x, target_y)

    def send_enter_key(self):
        """Sends native VK_RETURN (Enter) keypress to submit focused modal dialog."""
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
        Captures entire virtual desktop across all monitors and scales coordinates
        correctly to account for mixed DPI scaling on casted displays.
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

            # Calculate DPI scale factor between captured image pixels and virtual desktop units
            scale_x = vw / img_w if img_w else 1.0
            scale_y = vh / img_h if img_h else 1.0

            # Scan the image in rows
            for y in range(40, img_h - 40, 5):
                streak = 0
                start_x = 0
                for x in range(40, img_w - 40, 4):
                    r, g, b = screenshot.getpixel((x, y))[:3]
                    # Blue button detection with cast compression tolerance
                    if r < 105 and 70 <= g <= 200 and 150 <= b <= 255 and (b > r + 45) and (b >= g + 8):
                        if streak == 0:
                            start_x = x
                        streak += 4
                    else:
                        if 30 <= streak <= 220:
                            cx_img = start_x + streak // 2
                            cy_img = y

                            # Verify button vertical thickness
                            h_count = 0
                            for check_y in range(max(0, cy_img - 26), min(img_h, cy_img + 26), 2):
                                pr, pg, pb = screenshot.getpixel((cx_img, check_y))[:3]
                                if pr < 105 and 70 <= pg <= 200 and 150 <= pb <= 255 and (pb > pr + 40):
                                    h_count += 2

                            if 14 <= h_count <= 62:
                                # Verify dark modal background to the left
                                dark_matches = 0
                                for check_x in range(max(0, cx_img - 240), cx_img - 40, 15):
                                    dr, dg, db = screenshot.getpixel((check_x, cy_img))[:3]
                                    if dr < 70 and dg < 70 and db < 80:
                                        dark_matches += 1

                                if dark_matches >= 3:
                                    # Convert image pixel coordinates to normalized virtual desktop coordinates
                                    screen_x = vx + int(cx_img * scale_x) + self.x_offset.get()
                                    screen_y = vy + int(cy_img * scale_y) + self.y_offset.get()
                                    return (screen_x, screen_y)
                        streak = 0
            return None
        except Exception:
            return None

    def test_scan_screens(self):
        """Scans all screens and reports exact coordinates found."""
        self.status_text.configure(text="Scanning all screens...", fg="#88c0d0")
        self.root.update()

        pos = self.find_submit_button_on_screen()
        if pos:
            self.last_detected_pos = pos
            sx, sy = pos
            self.play_chime()
            screen_name = "Screen 2 (Extended Cast)" if sx >= 1536 else "Screen 1 (Primary)"
            self.coord_lbl.configure(
                text=f"Found: ({sx}, {sy}) on {screen_name}. Click '🎯 Click Detected Pos' to test.",
                fg="#57f287"
            )
            self.status_text.configure(text=f"Detected on {screen_name}!", fg="#57f287")
            messagebox.showinfo("Scanner Result", f"✅ Found Submit button at:\n\nX: {sx}, Y: {sy}\nDisplay: {screen_name}\n\nYou can click '🎯 Click Detected Pos' to test-click it now!")
        else:
            self.coord_lbl.configure(text="No Submit button detected right now.", fg="#f04747")
            self.status_text.configure(text="No button detected", fg="#f04747")
            messagebox.showwarning("Scanner Result", "❌ No Submit button detected.\n\nMake sure an Antigravity confirmation modal is currently visible on either screen.")

    def test_click_detected(self):
        """Test-clicks the detected position so the user can verify mouse placement."""
        if not self.last_detected_pos:
            self.test_scan_screens()

        if self.last_detected_pos:
            sx, sy = self.last_detected_pos
            self.click_virtual_desktop(sx, sy)
            time.sleep(0.05)
            self.send_enter_key()
            self.play_chime()
            messagebox.showinfo("Test Click", f"🎯 Clicked at ({sx}, {sy}) and sent Enter key!")

    def execute_approval(self, cx, cy):
        """Executes the approval with precision click + Enter key fallback."""
        prev_active_hwnd = user32.GetForegroundWindow()
        orig_mouse_x, orig_mouse_y = pyautogui.position()

        # If Option 4 (Always Allow) is selected, click Option 4 row first
        if self.selected_mode.get() == "always_allow":
            opt4_x = max(10, cx - 220)
            opt4_y = max(10, cy - 50)
            self.click_virtual_desktop(opt4_x, opt4_y)
            time.sleep(0.12)

        # 1. Deliver Win32 virtual desktop click
        self.click_virtual_desktop(cx, cy)
        time.sleep(0.04)

        # 2. Also send Enter key to guarantee submission
        self.send_enter_key()
        self.click_count += 1

        # 3. Restore mouse cursor and user's previous active window
        if self.stealth_enabled.get():
            pyautogui.moveTo(orig_mouse_x, orig_mouse_y)
            if prev_active_hwnd:
                user32.SetForegroundWindow(prev_active_hwnd)

        # 4. Play loud chime
        if self.sound_enabled.get():
            self.play_chime()

        self.root.after(0, lambda c=self.click_count: self.count_lbl.configure(text=f"Approved: {c}"))
        self.root.after(0, lambda pos=(cx, cy): self.coord_lbl.configure(text=f"Last approved at ({pos[0]}, {pos[1]})", fg="#5865f2"))

    def detection_loop(self):
        while self.is_running:
            try:
                btn_pos = self.find_submit_button_on_screen()
                if btn_pos and self.is_running:
                    cx, cy = btn_pos
                    time.sleep(self.delay_var.get())
                    self.execute_approval(cx, cy)
                    time.sleep(1.3)
                else:
                    time.sleep(0.6)
            except Exception:
                time.sleep(1.0)

    def start_hotkey_listener(self):
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
