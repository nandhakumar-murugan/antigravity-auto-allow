import uiautomation as auto

print("uiautomation version:", auto.VERSION)

# Search for Antigravity window
ag_win = None
for w in auto.GetRootControl().GetChildren():
    name = w.Name
    class_name = w.ClassName
    # Check if Antigravity is in title or process
    if "antigravity" in name.lower() or "antigravity" in class_name.lower():
        print(f"Found Window: Name='{name}', Class='{class_name}', Rect={w.BoundingRectangle}")
        ag_win = w

if not ag_win:
    # Try finding by ProcessId
    import psutil
    for p in psutil.process_iter(['pid', 'name']):
        if "antigravity" in (p.info['name'] or '').lower():
            w = auto.WindowControl(searchDepth=1, ProcessId=p.info['pid'])
            if w.Exists(maxSearchSeconds=0.5):
                print(f"Found Window by PID: Name='{w.Name}', Rect={w.BoundingRectangle}")
                ag_win = w
                break

if ag_win:
    # Search for Submit button inside Antigravity window
    btn = ag_win.ButtonControl(searchDepth=15, Name="Submit")
    if btn.Exists(maxSearchSeconds=1):
        print(f"FOUND SUBMIT BUTTON! Name='{btn.Name}', Rect={btn.BoundingRectangle}")
    else:
        print("Submit button not found directly. Let's list buttons:")
        for b in ag_win.GetChildren():
            print("Child:", b.ControlTypeName, b.Name)
else:
    print("Antigravity window not found via UIA in current session")
