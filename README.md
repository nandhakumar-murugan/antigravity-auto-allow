# Antigravity Auto-Allow Companion (Precision Calibration & Multi-Screen Edition)

A floating on-screen desktop tool created specifically to solve confirmation fatigue when running agent tasks in Google Antigravity.

---

## 🏷️ Versions & Changelog

### **v1.4.0 (Precision Calibration Edition - Latest)**
- **DPI-Aware Coordinate Normalization**: Automatically converts physical captured pixels into normalized logical virtual desktop coordinates across mixed-DPI displays.
- **Win32 `MOUSEEVENTF_VIRTUALDESK` Clicker**: Uses native 64-bit Windows normalized absolute virtual mouse events (`0..65535`) to land with single-pixel accuracy on extended/cast displays.
- **Dual Action (Click + Enter Fallback)**: Delivers both the precision click and a native `VK_RETURN` (Enter) keypress. In Antigravity's dialog, Option 1 is pre-focused, so this guarantees 100% submission even if mouse calibration differs.
- **Diagnostic `🎯 Click Detected Pos`**: Allows you to instantly test-click the detected button coordinates to verify cursor placement with your own eyes.

### **v1.3.0**
- Dual-Laptop / Extended Cast Support across all connected screens (`all_screens=True`).
- Tolerant Color Engine for Wi-Fi video streaming compression.
- Live Screen Scanner button.

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
