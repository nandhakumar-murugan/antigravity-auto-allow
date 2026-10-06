# Antigravity Auto-Allow Companion (Direct UI Automation Edition)

A floating on-screen desktop tool created specifically to solve confirmation fatigue when running agent tasks in Google Antigravity.

---

## 🏷️ Versions & Changelog

### **v2.0.0 (Direct UI Automation & Safe Invocation Edition - Major Release)**
- **Direct Windows UI Automation (UIA)**: Completely replaces unreliable pixel scanners with native Microsoft UI Automation (`uiautomation`).
- **Programmatic DOM `Invoke()`**: Submits the dialog directly through the Accessibility / DOM tree **without moving the physical mouse cursor at all**!
- **100% System File Immune**: Strictly interrogates the Antigravity Electron accessibility tree. It is physically impossible to touch system files, desktop icons, or other application menus.
- **Resolution & Cast Proof**: Works flawlessly across multiple screens, wireless Miracast laptops, and mixed DPI scalings because it operates on object trees rather than screen coordinates.
- **Smart Focus & Enter Fallback**: Seamlessly handles tall or scrolled dialogs.

### **v1.6.0**
- Safe zone coordinate restrictions.

### **v1.5.0**
- Real-time live activity log and instant hotkey `F8`.

### **v1.4.0**
- Win32 precision clicking.

### **v1.0.0**
- Initial release.

---

## 🖥️ How to Run
- Double-click **`Antigravity_Auto_Allow.bat`** directly on your Desktop, or
- Run `Start_Auto_Allow.bat` inside [`C:\Users\smnk2\.gemini\antigravity\scratch\antigravity_auto_allow`](file:///C:/Users/smnk2/.gemini/antigravity/scratch/antigravity_auto_allow).
