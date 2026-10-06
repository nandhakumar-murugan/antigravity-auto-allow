# Antigravity Auto-Allow Companion (Ultra-Tolerant Multi-Screen Edition)

A floating on-screen desktop tool created specifically to solve confirmation fatigue when running agent tasks in Google Antigravity.

---

## 🏷️ Versions & Changelog

### **v1.5.0 (Ultra-Tolerant Engine & Live Activity Log - Latest)**
- **Ultra-Tolerant Color Matching**: Removed fragile dark background requirements. Easily catches blue Submit buttons across Wi-Fi cast compression, varied screen brightness, and custom themes.
- **Direct Win32 Hardware Cursor Movement**: Uses `win32api.SetCursorPos` and `mouse_event` for direct native clicking across any multi-monitor virtual coordinates.
- **Live Activity Log Box**: Shows real-time status right on the widget face (e.g. `[18:48:02] Scanning...`, `[18:48:03] Detected button at (2540, 515)...`).
- **Instant Hotkey (`F8`)**: Press `F8` from anywhere to immediately submit/approve the open Antigravity dialog with zero delay.
- **`🎯 Force Click Submit`**: Diagnostic button to test-click or trigger Enter on the dialog instantly.

### **v1.4.0**
- Win32 virtual mouse precision clicker, DPI normalization, Enter fallback.

### **v1.3.0**
- Dual-Laptop / Extended Cast Support across all connected screens (`all_screens=True`).

### **v1.2.0**
- Semantic version badges and release tags.

### **v1.1.0**
- Zero-disruption background mode with instant cursor and browser window refocus.
- Loud alert chime (`1300 Hz -> 1850 Hz`).

### **v1.0.0**
- Initial release with floating widget, hotkey `F9`, Option 1 & 4 support.

---

## 🖥️ How to Run
- Double-click **`Antigravity_Auto_Allow.bat`** directly on your Desktop, or
- Run `Start_Auto_Allow.bat` inside [`C:\Users\smnk2\.gemini\antigravity\scratch\antigravity_auto_allow`](file:///C:/Users/smnk2/.gemini/antigravity/scratch/antigravity_auto_allow).
