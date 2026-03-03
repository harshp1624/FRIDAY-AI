import os
import subprocess
import ctypes
import psutil
import pyautogui
import time

# Robust mapping for common ambiguous app names to their Windows executable files
APP_MAP = {
    "task manager": "taskmgr.exe",
    "calculator": "calc.exe",
    "notepad": "notepad.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "spotify": "spotify.exe",
    "file explorer": "explorer.exe",
    "command prompt": "cmd.exe",
    "terminal": "wt.exe",
    "settings": "ms-settings:"
}

class OSEngine:
    def __init__(self):
        # Configure PyAutoGUI failsafes
        pyautogui.FAILSAFE = True

    def lock_workstation(self):
        """Locks the Windows workstation"""
        try:
            ctypes.windll.user32.LockWorkStation()
            return "System locked successfully."
        except Exception as e:
            return f"Failed to lock system: {str(e)}"

    def sleep_system(self):
        """Puts the Windows system to sleep"""
        try:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "Entering sleep mode."
        except Exception as e:
            return f"Failed to sleep system: {str(e)}"

    def shutdown_system(self, delay_seconds=10):
        """Initiates a system shutdown"""
        try:
            os.system(f"shutdown /s /t {delay_seconds}")
            return f"System will shut down in {delay_seconds} seconds."
        except Exception as e:
            return f"Failed to initiate shutdown: {str(e)}"

    def restart_system(self, delay_seconds=10):
        """Initiates a system restart"""
        try:
            os.system(f"shutdown /r /t {delay_seconds}")
            return f"System will restart in {delay_seconds} seconds."
        except Exception as e:
            return f"Failed to initiate restart: {str(e)}"
            
    def cancel_shutdown(self):
        """Cancels a pending shutdown or restart"""
        try:
            os.system("shutdown /a")
            return "Shutdown sequence aborted."
        except Exception as e:
            return f"Failed to cancel shutdown: {str(e)}"

    def get_system_health(self):
        """Returns the current CPU and RAM usage"""
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        plugged = battery.power_plugged if battery else False
        battery_percent = battery.percent if battery else "N/A"
        
        status = f"CPU is at {cpu_usage}%. RAM is at {ram_usage}%. "
        if battery:
            status += f"Battery is at {battery_percent}%, "
            status += "plugged in." if plugged else "running on battery."
        return status

    def _get_executable(self, app_name: str) -> str:
        """Helper to map spoken natural language apps to windows executables."""
        clean_name = app_name.lower().strip()
        return APP_MAP.get(clean_name, clean_name)

    def open_app(self, app_name: str):
        """Opens a Windows application"""
        try:
            exe_name = self._get_executable(app_name)
            
            # Special handling for ms-settings which isn't an exe
            if exe_name.startswith("ms-"):
                os.system(f'start {exe_name}')
            else:
                # The 'start' command works well for common executable names and URLs
                os.system(f'start "" "{exe_name}"')
            return f"Opening application: {app_name} ({exe_name})"
        except Exception as e:
            return f"Failed to open application: {str(e)}"

    def close_app(self, app_name: str):
        """Forcefully kills a Windows application process."""
        try:
            exe_name = self._get_executable(app_name)
            # Ensure it ends with .exe for taskkill if it's not a special URI
            if not exe_name.endswith(".exe") and not exe_name.startswith("ms-"):
                exe_name += ".exe"
                
            # /f (force) /im (image name) /t (kill child processes)
            result = os.system(f'taskkill /f /im "{exe_name}" /t')
            if result == 0:
                return f"Successfully closed {app_name}."
            else:
                return f"Could not find or close {app_name}. It may not be running."
        except Exception as e:
            return f"Failed to close application: {str(e)}"
            
    def type_text(self, text: str):
        """Simulates keyboard typing to write strings out on the screen."""
        try:
            # Add a tiny delay so user can ensure focus is correct
            time.sleep(0.5)
            # Type the text with a natural human-like delay
            pyautogui.write(text, interval=0.02)
            return f"Successfully typed out the text: '{text}'"
        except Exception as e:
            return f"Failed to type out text: {str(e)}"

    def execute_action(self, action_name: str, parameters: dict = None):
        """Routes string actions from the Brain Engine to OS commands."""
        action_name = action_name.lower().strip()
        
        if action_name == "lock_system":
            return self.lock_workstation()
        elif action_name == "sleep_system":
            return self.sleep_system()
        elif action_name == "shutdown_system":
            delay = parameters.get("delay", 10) if parameters else 10
            return self.shutdown_system(delay)
        elif action_name == "restart_system":
            delay = parameters.get("delay", 10) if parameters else 10
            return self.restart_system(delay)
        elif action_name == "cancel_shutdown":
            return self.cancel_shutdown()
        elif action_name == "check_health":
            return self.get_system_health()
        elif action_name == "open_app":
            app_name = parameters.get("app_name", "") if parameters else ""
            if app_name:
                return self.open_app(app_name)
            return "Application name not provided."
        elif action_name == "close_app":
            app_name = parameters.get("app_name", "") if parameters else ""
            if app_name:
                return self.close_app(app_name)
            return "Application name not provided for closing."
        elif action_name == "type_text":
            text = parameters.get("text_to_type", "") if parameters else ""
            if text:
                return self.type_text(text)
            return "No text provided to type."
        else:
            return "Action not recognized by OSEngine."

if __name__ == "__main__":
    # Test block
    engine = OSEngine()
    print("Health:", engine.get_system_health())
