# Antigravity Auto-Allow Companion (Multi-Monitor & Cast Edition)

A floating on-screen desktop tool created specifically to solve confirmation fatigue when running agent tasks in Google Antigravity.

---

## 🏷️ Versions & Changelog

### **v1.3.0 (Dual-Laptop / Extended Cast Edition - Latest)**
- **Dual-Laptop / Cast Support**: Full support for extended monitors via Windows Cast / Miracast.
- **Virtual Coordinate Mapping**: Uses `SM_XVIRTUALSCREEN` and `SM_YVIRTUALSCREEN` to accurately click anywhere across multiple screens.
- **Tolerant Color Matching**: Accommodates Miracast video compression artifacts on wireless secondary displays.
- **Bounding Box Validation**: Target-locks to Antigravity window boundaries across all monitors.
- **Diagnostic Test Scanner**: Added `🔍 Test Scan Screens` button to verify detection live across all displays.

### **v1.2.0**
- Added clickable semantic version pill badge (`v1.2.0`) in header and version info modal.
- Structured `__version__`, `__author__`, and release tags.

### **v1.1.0**
- Antigravity process target lock (`Antigravity.exe` only).
- Zero-disruption background mode with instant cursor and browser window refocus.
- Loud alert chime (`1300 Hz -> 1850 Hz`).

### **v1.0.0**
- Initial release with floating widget, hotkey `F9`, Option 1 & 4 support.

---

## 🖥️ How to Run
- Double-click **`Antigravity_Auto_Allow.bat`** directly on your Desktop, or
- Run `Start_Auto_Allow.bat` inside [`C:\Users\smnk2\.gemini\antigravity\scratch\antigravity_auto_allow`](file:///C:/Users/smnk2/.gemini/antigravity/scratch/antigravity_auto_allow).
