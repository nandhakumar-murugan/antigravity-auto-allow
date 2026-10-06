# Antigravity Auto-Allow Companion (Antigravity.exe Process Locking Edition)

A floating on-screen desktop tool created specifically to solve confirmation fatigue when running agent tasks in Google Antigravity.

---

## 🏷️ Versions & Changelog

### **v2.1.0 (Antigravity.exe Process Target Locking - Latest)**
- **Self-Target Exclusion**: Explicitly excludes the companion widget window (`auto-allow`) from window lookups so it never targets itself.
- **Strict `Antigravity.exe` Process Match**: Targets the real Electron application window by its unique process name (`Antigravity.exe`), immediately locating the actual active conversation window.
- **Deep DOM Button Search**: Traverses up to 30 levels of the accessibility tree to find the bright blue `[ Submit ]` button inside Antigravity's dialog card.
- **Zero-Disruption Fallback**: Focuses the real Antigravity window and delivers native `Enter` keypress if the button is scrolled, instantly submitting Option 1 (*"Yes, allow this time"*).

### **v2.0.0**
- Direct Windows UI Automation (UIA) DOM invocation.

### **v1.6.0**
- Safe zone coordinate restrictions.

### **v1.5.0**
- Real-time live activity log and instant hotkey `F8`.

---

## 🖥️ How to Run
- Double-click **`Antigravity_Auto_Allow.bat`** directly on your Desktop, or
- Run `Start_Auto_Allow.bat` inside [`C:\Users\smnk2\.gemini\antigravity\scratch\antigravity_auto_allow`](file:///C:/Users/smnk2/.gemini/antigravity/scratch/antigravity_auto_allow).
