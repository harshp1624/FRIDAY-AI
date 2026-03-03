import os
from win32com.client import Dispatch

desktop = os.path.expanduser('~\\Desktop')
path = os.path.join(desktop, "F.R.I.D.A.Y.lnk")
target = r"c:\Users\harsh\OneDrive\Desktop\FRIDAY\dist\F.R.I.D.A.Y.exe"
wDir = r"c:\Users\harsh\OneDrive\Desktop\FRIDAY\dist"
icon = r"c:\Users\harsh\OneDrive\Desktop\FRIDAY\icon.ico"

print(f"Creating shortcut at {path} pointing to {target}")

shell = Dispatch('WScript.Shell')
shortcut = shell.CreateShortCut(path)
shortcut.Targetpath = target
shortcut.WorkingDirectory = wDir
shortcut.IconLocation = icon
shortcut.save()
print("Shortcut created successfully.")
