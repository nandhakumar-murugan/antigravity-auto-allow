import psutil
import uiautomation as auto

root = auto.GetRootControl()

print("Searching for real Antigravity.exe top-level windows:")
for child in root.GetChildren():
    pid = child.ProcessId
    try:
        proc = psutil.Process(pid)
        pname = proc.name()
    except Exception:
        pname = ""

    if "antigravity" in pname.lower():
        print(f"HWND: {child.NativeWindowHandle}, PID: {pid}, Proc: {pname}, Name: '{child.Name}', Class: '{child.ClassName}'")
        # Search for Submit button inside this window
        btn = child.ButtonControl(searchDepth=25, Name="Submit")
        if btn.Exists(maxSearchSeconds=0.2):
            print(f"  --> FOUND SUBMIT BUTTON! Rect={btn.BoundingRectangle}")
