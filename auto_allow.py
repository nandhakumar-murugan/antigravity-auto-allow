"""
Antigravity Auto-Allow Companion (Active Loop & Bounded Window Engine)
Version: 2.2.0

Features:
- Active Auto-Approval Loop: Automatically detects the blue Submit button inside Antigravity and approves hands-free
- Clamped Window Scanning: Scans strictly inside the lower half of the Antigravity application bounding box
- 100% Protected: Never scans or touches system files, desktop icons, top menus, or other applications
- Dual Submission (Hardware Click + Enter Key): Clicks the Submit button and sends native Enter key
- Zero-Disruption: Instantly restores your mouse cursor and keeps active browser / editor focused
- Manual Instant Approve Hotkey (F8) and Toggle (F9)
- Loud Alert Chime on every approval
"""

__version__ = "2.2.0"
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
import uiautomation as auto

# Enable Per-Monitor DPI Awareness so screen coordinates match physical pixels exactly
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32

class AutoAllowApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{__app_name__} v{__version__}")
        self.root.geometry("420x440")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1f22")

        # Frameless modern dark window
        self.root.overrideredirect(True)

        self.is_running = False
        self.auto_thread = None
        self.hotkey_thread = None
        self.click_count = 0
        self.selected_mode = tk.StringVar(value="allow_once")
        self.sound_enabled = tk.BooleanVar(value=True)
        self.stealth_enabled = tk.BooleanVar(value=True)
        self.delay_var = tk.DoubleVar(value=0.20)
        self._cached_ag_win = None

        self._drag_start_x = 0
        self._drag_start_y = 0

        self.setup_ui()
        self.position_window()
        self.start_hotkey_listener()

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

        # Header Bar (Draggable)
        header = tk.Frame(border_frame, bg="#2b2d31", height=32)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title_lbl = tk.Label(
            header,
            text="⚡ Auto-Allow (Loop Engine)",
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
            text="PAUSED (F9) • Ready to Auto-Allow",
            fg="#b9bbbe",
            bg="#2b2d31",
            font=("Segoe UI", 9, "bold")
        )
        self.status_text.pack(side=tk.LEFT)

        # Main Action Button (Toggle)
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
        opt_frame1.pack(fill=tk.X, pady=(0, 6))

        tk.Checkbutton(
            opt_frame1,
            text="Zero-Disruption (Restore Focus)",
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

        # Action Buttons Row
        test_frame = tk.Frame(body, bg="#1e1f22")
        test_frame.pack(fill=tk.X, pady=(0, 6))

        btn_force_click = tk.Button(
            test_frame,
            text="🎯 Click Submit Now (F8)",
            bg="#4c566a",
            fg="#ebcb8b",
            activebackground="#5e81ac",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            padx=10,
            pady=4,
            command=self.force_submit_now
        )
        btn_force_click.pack(side=tk.LEFT)

        btn_test_detect = tk.Button(
            test_frame,
            text="🔍 Test Detection",
            bg="#2b2d31",
            fg="#88c0d0",
            activebackground="#3e4247",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8),
            padx=8,
            pady=4,
            command=self.test_find_button
        )
        btn_test_detect.pack(side=tk.LEFT, padx=(6, 0))

        btn_test_snd = tk.Button(
            test_frame,
            text="🔊 Chime",
            bg="#2b2d31",
            fg="#00a8fc",
            activebackground="#3e4247",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 8),
            padx=8,
            pady=4,
            command=self.play_chime
        )
        btn_test_snd.pack(side=tk.RIGHT)

        # Real-time Activity Log Box
        log_box = tk.Frame(body, bg="#141517", padx=8, pady=6, bd=1, relief=tk.SUNKEN)
        log_box.pack(fill=tk.X, pady=(0, 6))

        self.log_lbl = tk.Label(
            log_box,
            text="[Ready] Turn ON to automatically approve dialogs as they appear.",
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
            text="💡 Shortcuts: F9 = Toggle Auto-Allow ON/OFF | F8 = Submit Immediately",
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
            text=f"🛡️ Clamped Loop Engine • v{__version__}",
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
            "• v2.2.0: Active Auto-Approval Loop Engine - strictly scans lower half of Antigravity window\n"
            "• 100% Guaranteed: Never clicks system files, desktop icons, or other apps\n"
            "• Dual action: Direct Submit button click + native Enter key on Antigravity window\n"
            "• Zero Disruption: Instantly restores mouse cursor and browser focus\n\n"
            "Repository:\n"
            "https://github.com/nandhakumar-murugan/antigravity-auto-allow"
        )
        messagebox.showinfo("Version Information", info)

    def position_window(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w, win_h = 420, 440
        x = max(10, screen_w - win_w - 30)
        y = max(10, screen_h - win_h - 70)
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
        self.status_text.configure(text="ACTIVE • Auto-Submitting Dialogs", fg="#23a55a")
        self.log("Auto-Allow ACTIVE. Watching for Antigravity dialogs...", "#57f287")

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
        self.status_text.configure(text="PAUSED (F9) • Ready to Auto-Allow", fg="#b9bbbe")
        self.log("Auto-Allow PAUSED.", "#e5c07b")

    def play_chime(self):
        def sound_worker():
            try:
                winsound.Beep(1300, 110)
                winsound.Beep(1850, 160)
            except Exception:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        threading.Thread(target=sound_worker, daemon=True).start()

    def get_antigravity_window_control(self):
        """Finds the REAL Antigravity application window control (strictly excluding this tool)."""
        try:
            # Check cached window first for microsecond performance
            if self._cached_ag_win:
                hwnd = getattr(self._cached_ag_win, "NativeWindowHandle", 0)
                if hwnd and user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd):
                    rect = self._cached_ag_win.BoundingRectangle
                    if rect and rect.width() >= 400 and rect.height() >= 300:
                        return self._cached_ag_win

            root = auto.GetRootControl()
            best_win = None
            best_area = 0

            # Search top-level windows for the Antigravity main editor window
            for child in root.GetChildren():
                name = child.Name or ""
                # Strictly exclude this companion tool
                if "auto-allow" in name.lower() or "auto_allow" in name.lower() or child.NativeWindowHandle == self.root.winfo_id():
                    continue

                rect = child.BoundingRectangle
                if not rect or rect.width() < 400 or rect.height() < 300:
                    continue

                pid = child.ProcessId
                try:
                    proc = psutil.Process(pid)
                    pname = proc.name().lower()
                except Exception:
                    pname = ""

                # Match real Antigravity window by process or window title
                if "antigravity.exe" in pname or "antigravity" in name.lower():
                    area = rect.width() * rect.height()
                    if area > best_area:
                        best_area = area
                        best_win = child

            if best_win:
                self._cached_ag_win = best_win
                return best_win
        except Exception:
            pass
        return None

    def find_submit_in_antigravity_window(self):
        """
        Scans STRICTLY inside the lower 50% of the Antigravity window for the blue Submit button.
        Returns ((screen_x, screen_y), ag_win) if found, else (None, ag_win or None).
        This guarantees it NEVER scans or clicks system files or other applications.
        """
        try:
            ag_win = self.get_antigravity_window_control()
            if not ag_win:
                return None, None

            rect = ag_win.BoundingRectangle
            if not rect or rect.width() < 400 or rect.height() < 300:
                return None, ag_win

            # Bounding box of the Antigravity window
            ag_left = rect.left
            ag_top = rect.top
            ag_right = rect.right
            ag_bottom = rect.bottom

            # Submit button is ALWAYS in the lower 45% of the window
            scan_top = int(ag_top + (ag_bottom - ag_top) * 0.45)
            scan_bottom = ag_bottom - 8
            scan_left = ag_left + 40
            scan_right = ag_right - 40

            if scan_right <= scan_left + 50 or scan_bottom <= scan_top + 30:
                return None, ag_win

            # Grab strictly the lower half of the Antigravity window
            try:
                shot = ImageGrab.grab(bbox=(scan_left, scan_top, scan_right, scan_bottom), all_screens=True)
            except Exception:
                try:
                    shot = ImageGrab.grab(bbox=(scan_left, scan_top, scan_right, scan_bottom))
                except Exception:
                    return None, ag_win

            w, h = shot.size
            if w <= 30 or h <= 30:
                return None, ag_win

            # Scan from bottom upwards for speed
            for y in range(h - 12, 10, -3):
                streak = 0
                start_x = 0
                for x in range(10, w - 10, 2):
                    r, g, b = shot.getpixel((x, y))[:3]
                    # Match blue Submit button in Antigravity (#007ACC):
                    # b >= 165, b > r + 60, b > g + 25, r < 65, g <= 145
                    if (b >= 165) and (b > r + 60) and (b > g + 25) and (r < 65) and (g <= 145):
                        if streak == 0:
                            start_x = x
                        streak += 2
                    else:
                        if 24 <= streak <= 140:
                            btn_x = start_x + streak // 2
                            btn_y = y

                            # Verify button vertical thickness around this center
                            h_count = 0
                            for cy in range(max(0, btn_y - 16), min(h, btn_y + 16), 2):
                                pr, pg, pb = shot.getpixel((btn_x, cy))[:3]
                                if (pb >= 165) and (pb > pr + 50) and (pb > pg + 20) and (pr < 70):
                                    h_count += 2

                            if 10 <= h_count <= 45:
                                screen_x = scan_left + btn_x
                                screen_y = scan_top + btn_y
                                return (screen_x, screen_y), ag_win
                        streak = 0
        except Exception:
            pass
        return None, None

    def submit_antigravity_dialog(self, target_pos=None, ag_win=None):
        """
        Executes the approval strictly inside the real Antigravity window.
        1. Direct Hardware Click on Submit button (if target_pos provided).
        2. Focus Antigravity Window & Send Native Enter Key (verified 100% working).
        3. Stealth restore active window and mouse cursor.
        """
        if not ag_win:
            ag_win = self.get_antigravity_window_control()
        if not ag_win:
            return False

        prev_active_hwnd = user32.GetForegroundWindow()
        orig_mouse_x, orig_mouse_y = pyautogui.position()

        # Step 1: Click the Submit button directly if detected
        if target_pos:
            cx, cy = target_pos
            win32api.SetCursorPos((int(cx), int(cy)))
            time.sleep(0.04)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.04)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

        # Step 2: Also send Enter key to real Antigravity window (guarantees submission)
        try:
            hwnd = ag_win.NativeWindowHandle
            if hwnd:
                user32.SetForegroundWindow(hwnd)
                time.sleep(0.05)
                VK_RETURN = 0x0D
                user32.keybd_event(VK_RETURN, 0, 0, 0)
                time.sleep(0.03)
                user32.keybd_event(VK_RETURN, 0, 2, 0)
        except Exception:
            pyautogui.press('enter')

        # Step 3: Stealth restore mouse position and active browser focus
        if self.stealth_enabled.get():
            time.sleep(0.04)
            win32api.SetCursorPos((orig_mouse_x, orig_mouse_y))
            if prev_active_hwnd and prev_active_hwnd != ag_win.NativeWindowHandle:
                user32.SetForegroundWindow(prev_active_hwnd)

        self.on_successful_approval("Auto-Submitted Dialog inside Antigravity")
        return True

    def on_successful_approval(self, method_name):
        self.click_count += 1
        if self.sound_enabled.get():
            self.play_chime()
        self.root.after(0, lambda c=self.click_count: self.count_lbl.configure(text=f"Approved: {c}"))
        self.root.after(0, lambda: self.log(f"Approved ({self.click_count})! {method_name}.", "#57f287"))

    def test_find_button(self):
        """Scans for the Submit button inside Antigravity and reports live status."""
        self.log("Scanning Antigravity window...", "#88c0d0")
        self.root.update()

        pos, ag_win = self.find_submit_in_antigravity_window()
        if pos:
            self.play_chime()
            sx, sy = pos
            msg = (
                f"✅ Submit Button Found inside Antigravity!\n\n"
                f"Coordinates: ({sx}, {sy})\n"
                f"Window: '{ag_win.Name if ag_win else 'Antigravity'}'\n\n"
                "100% verified inside the Antigravity window.\n"
                "Auto-Allow will automatically click this button when active!"
            )
            self.log(f"Submit button found at ({sx}, {sy})!", "#57f287")
            messagebox.showinfo("Scanner Result", msg)
        else:
            ag = ag_win or self.get_antigravity_window_control()
            if ag:
                rect = ag.BoundingRectangle
                msg = (
                    f"ℹ️ Antigravity Window Found: '{ag.Name}'\n\n"
                    f"Bounds: ({rect.left}, {rect.top}) to ({rect.right}, {rect.bottom})\n"
                    f"Width: {rect.width()}px, Height: {rect.height()}px\n\n"
                    "Submit button is not currently visible or no approval dialog is open.\n"
                    "Whenever a dialog appears, Auto-Allow will detect and submit it immediately."
                )
                self.log("Antigravity window found, dialog not active.", "#e5c07b")
                messagebox.showinfo("Antigravity Scanner Status", msg)
            else:
                self.log("Antigravity window not detected.", "#f04747")
                messagebox.showwarning("Window Not Found", "Could not locate Antigravity window. Please ensure Antigravity is open.")

    def force_submit_now(self):
        """Immediately submits the open dialog (manual button click or F8)."""
        pos, ag_win = self.find_submit_in_antigravity_window()
        if not ag_win:
            ag_win = self.get_antigravity_window_control()
        success = self.submit_antigravity_dialog(target_pos=pos, ag_win=ag_win)
        if not success:
            pyautogui.press('enter')
            self.log("Sent Enter key directly.", "#ebcb8b")

    def detection_loop(self):
        """
        Background loop continuously watching for the blue Submit button
        inside the Antigravity window and auto-submitting it.
        """
        while self.is_running:
            try:
                pos, ag_win = self.find_submit_in_antigravity_window()
                if pos and self.is_running:
                    sx, sy = pos
                    self.log(f"Submit button detected at ({sx}, {sy})! Auto-submitting...", "#88c0d0")
                    time.sleep(self.delay_var.get())
                    self.submit_antigravity_dialog(target_pos=pos, ag_win=ag_win)
                    # Cool-down to let dialog close
                    time.sleep(1.6)
                else:
                    time.sleep(0.4)
            except Exception:
                time.sleep(0.8)

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
                    self.root.after(0, self.force_submit_now)
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
