# Antigravity Auto-Allow Companion (Background Stealth Edition)

A floating on-screen desktop tool created specifically to solve confirmation fatigue when running agent tasks in Google Antigravity.

---

## 🏷️ Versions & Changelog

### **v1.2.0 (Latest Release)**
- **UI Version Badges**: Added clickable semantic version pill badge (`v1.2.0`) in header and version info modal.
- **Metadata**: Added structured `__version__`, `__author__`, and release tags for tracking.
- **Refined Layout**: Optimized widget geometry and spacing.

### **v1.1.0**
- **Target Lock**: Strict check on process ID and window identity (`Antigravity.exe`). Completely ignores browser windows, Chrome, VS Code, etc.
- **Zero-Disruption Background Mode**: Automatically restores mouse cursor position and foreground application focus in milliseconds after clicking.
- **Loud Alert Chime**: High-decibel dual-tone chime (`1300 Hz -> 1850 Hz`) on every approval click with preview button.

### **v1.0.0**
- Initial release featuring on-screen floating toggle widget.
- Support for `Allow This Time` (Option 1) and `Always Allow` (Option 4).
- Global hotkey `F9` for one-touch toggle control.

---

## 🚀 Key Features

1. **Target-Locked to Antigravity**:
   - Strictly checks window process identity (`Antigravity.exe`).
   - Never clicks inside Google Chrome, Firefox, Edge, VS Code, or any other open applications.
2. **Zero-Disruption Background Mode**:
   - If you switch away to a web browser or another app while Antigravity is running in the background, Auto-Allow executes the approval click and **instantly returns your mouse cursor and restores focus to your active browser window in milliseconds**.
   - Your typing and browsing flow is never interrupted.
3. **Loud Audible Chime**:
   - Plays a crisp, distinct dual-tone alert chime (`1300 Hz -> 1850 Hz`) through system speakers on every approval so you know Antigravity progressed even when you're looking at another screen or tab.
   - Includes a "Test Sound" button to verify chime volume.
4. **Global Toggle Hotkey (`F9`)**:
   - Press **`F9`** anytime to turn auto-allow ON or OFF without needing to switch windows.

---

## 🖥️ How to Run
- Double-click **`Antigravity_Auto_Allow.bat`** directly on your Desktop, or
- Run `Start_Auto_Allow.bat` inside [`C:\Users\smnk2\.gemini\antigravity\scratch\antigravity_auto_allow`](file:///C:/Users/smnk2/.gemini/antigravity/scratch/antigravity_auto_allow).
