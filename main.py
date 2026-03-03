import os
import threading
import time
import sys
import socket
import json
import subprocess
import itertools
from dotenv import load_dotenv

with open("friday_debug.log", "a") as f:
    f.write("F.R.I.D.A.Y. Started\n")

class DummyFile:
    def write(self, x):
        with open("friday_debug.log", "a") as f:
            f.write(str(x))
    def flush(self): pass

if sys.stdout is None:
    sys.stdout = DummyFile()
if sys.stderr is None:
    sys.stderr = DummyFile()

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

class Spinner:
    def __init__(self, message="Processing..."):
        self.spinner = itertools.cycle(['-', '\\', '|', '/'])
        self.message = message
        self.running = False
        self.thread = None

    def spin(self):
        while self.running:
            sys.stdout.write(f'\r{self.message} {next(self.spinner)}')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 2) + '\r')
        sys.stdout.flush()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

import pystray
from PIL import Image, ImageDraw

from brain_engine import BrainEngine
from voice_engine import VoiceEngine
from os_engine import OSEngine
from memory_engine import MemoryEngine

load_dotenv(".env")

class FridayCore:
    def __init__(self):
        print("Initializing F.R.I.D.A.Y. Core Systems...")
        self.os_engine = OSEngine()
        self.voice_engine = VoiceEngine()
        
        # Check if ChromaDB model exists, warn user if it's about to download
        chroma_path = os.path.expanduser("~/.cache/chroma/onnx_models/all-MiniLM-L6-v2")
        if not os.path.exists(chroma_path):
            print("First run detected: Downloading ChromaDB memory models...")
            self.voice_engine.speak("Boss, since this is my first boot, I am downloading my core memory models. The terminal will indicate processing status. Please wait.")
            
        self.brain_engine = BrainEngine()
        
        spinner = Spinner("Initializing Memory Models (This may take a moment)")
        spinner.start()
        try:
            self.memory_engine = MemoryEngine()
        finally:
            spinner.stop()
            print("\rMemory Models Initialized.                              ")
        
        self.is_running = False
        self.listening_thread = None
        self.widget_process = None
        
        # Idle tracking & State Management
        self.last_command_time = time.time()
        self.silenced_until = 0  # Timestamp until which FRIDAY is forced to be silent
        self.is_processing = False # True when executing a command or thinking
        
        # Setup UDP socket for sending UI updates
        self.udp_ip = "127.0.0.1"
        self.udp_port = 5005
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def update_ui_state(self, status: str):
        """Send state update to the transparent desktop widget via UDP"""
        try:
            message = json.dumps({"status": status}).encode('utf-8')
            self.sock.sendto(message, (self.udp_ip, self.udp_port))
        except Exception as e:
            print(f"Failed to update UI widget: {e}")
            
    def _start_widget(self):
        """Launch the standalone UI widget script"""
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1 # SW_NORMAL

            if getattr(sys, 'frozen', False):
                # Run the internal ui logic via the built executable CLI argument
                self.widget_process = subprocess.Popen([sys.executable, "--widget"], startupinfo=startupinfo)
            else:
                # Run the ui_widget.py using python executable normally
                widget_path = os.path.join(os.path.dirname(__file__), "ui_widget.py")
                if os.path.exists(widget_path):
                    self.widget_process = subprocess.Popen([sys.executable, widget_path], startupinfo=startupinfo)
        except Exception as e:
            print(f"Could not start UI widget: {e}")

    def start_listening_loop(self):
        self._start_widget()
        self.update_ui_state("Booting Systems...")
        time.sleep(1) # Let widget appear
        
        self.is_running = True
        self.update_ui_state("Listening...")
        self.voice_engine.speak("Good morning, Hrix. I've been monitoring the systems all night. We are fully operational.")
        
        while self.is_running:
            try:
                self.update_ui_state("Listening...")
                # Listen to user with a 2-second timeout to allow idle checking
                user_text = self.voice_engine.listen(timeout=2)
                
                if user_text:
                    try:
                        self.is_processing = True
                        self.update_ui_state(f"Processing: \"{user_text}\"")
                        self.last_command_time = time.time() # Reset idle timer
                        print(f"\n[USER] Heard: \"{user_text}\"")
                        # 1. Fetch relevant memory for context
                        context = self.memory_engine.search_memory(user_text)
                        
                        # 2. Store current query
                        self.memory_engine.store_memory("user", user_text)
                        
                        # 3. Process through Brain (Ollama)
                        spinner = Spinner("[BRAIN] Processing with memory context")
                        spinner.start()
                        try:
                            response_data = self.brain_engine.process_input(user_text, context)
                        finally:
                            spinner.stop()
                            print("\r[BRAIN] Processing complete.               ")
                        
                        speech = response_data.get("speech", "")
                        action = response_data.get("action", "none")
                        parameters = response_data.get("parameters", {})
                        
                        print(f"[BRAIN] Thought: {speech}")
                        
                        # 4. Speak response
                        if speech:
                            self.memory_engine.store_memory("friday", speech)
                            self.voice_engine.speak(speech)
                            
                        # 5. Execute OS Action if required
                        if action and action.lower() != "none":
                            if action.lower() == "silence_system":
                                duration_seconds = parameters.get("duration_seconds", 0) if parameters else 0
                                if duration_seconds > 0:
                                    self.silenced_until = time.time() + duration_seconds
                                    print(f"[F.R.I.D.A.Y.] Silenced for {duration_seconds} seconds.")
                                    self.update_ui_state(f"Silenced ({duration_seconds}s)")
                            else:
                                # Explicitly communicate the task she is doing over Voice
                                app_name = parameters.get("app_name", "") if parameters else ""
                                if action.lower() == "open_app" and app_name:
                                    self.voice_engine.speak(f"I am opening {app_name}, Boss.")
                                elif action.lower() == "check_health":
                                    self.voice_engine.speak("Checking system health now.")
                                else:
                                    formatted_action = action.replace('_', ' ')
                                    self.voice_engine.speak(f"Executing {formatted_action} now.")
                                    
                                self.update_ui_state(f"Executing: {action}")
                                print(f"[ACTION] Triggering: {action} with params {parameters}")
                                result = self.os_engine.execute_action(action, parameters)
                                print(f"[OS RESULT] {result}")
                    finally:
                        self.is_processing = False
                        self.last_command_time = time.time() # Reset timer after finishing action
                else:
                    # Logic for when nothing was heard/understood (idle check)
                    idle_time = time.time() - self.last_command_time
                    
                    # Only do idle ping if not currently processing, not silenced, and idle for > 60 seconds
                    if not self.is_processing and time.time() > self.silenced_until:
                        # Ensure we don't spam if FRIDAY is currently speaking or doing a task
                        if idle_time >= 60:
                            self.update_ui_state("Idle - Waiting for instructions")
                            # The loop naturally fails listening timeouts quickly, 
                            # so we can just trigger a short check-in every 60 seconds
                            self.last_command_time = time.time() # Reset it so it asks every 60 seconds roughly
                            print("\n[F.R.I.D.A.Y.] Interactive Idle Ping...")
                            self.voice_engine.speak("What are you doing boss? Or what do you want next?")
                    elif time.time() <= self.silenced_until:
                        self.update_ui_state("Silenced")

            except Exception as e:
                # If it's just a timeout from listening, it's expected, don't sleep
                if "WaitTimeoutError" not in str(type(e)):
                    print(f"\n[CRITICAL ERROR] Main Loop: {e}")
                    time.sleep(2) # Prevent rapid failure looping

    def stop(self):
        print("Shutting down F.R.I.D.A.Y. systems...")
        self.is_running = False
        self.update_ui_state("Shutting down...")
        self.voice_engine.speak("Powering down systems now. Goodbye, Boss.")
        if self.widget_process:
            self.widget_process.terminate()

def create_tray_icon(core: FridayCore):
    # Try to load the custom logo, fallback to drawn F if missing
    logo_path = get_resource_path("friday_ai_logo.png")
    if os.path.exists(logo_path):
        try:
            image = Image.open(logo_path)
            # Ensure the image is formatted properly for pystray
            image.thumbnail((64, 64), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Failed to load custom logo: {e}")
            image = _draw_fallback_icon()
    else:
        image = _draw_fallback_icon()

    def on_quit(icon, item):
        core.stop()
        icon.stop()
        
    def on_start(icon, item):
        if not core.is_running:
            core.listening_thread = threading.Thread(target=core.start_listening_loop, daemon=True)
            core.listening_thread.start()

    menu = pystray.Menu(
        pystray.MenuItem('Start Listening', on_start),
        pystray.MenuItem('Quit', on_quit)
    )

    icon = pystray.Icon("FRIDAY", image, "FRIDAY AI", menu)
    return icon

def _draw_fallback_icon():
    width = 64
    height = 64
    color1 = (0, 0, 0)
    color2 = (0, 200, 255) # F.R.I.D.A.Y. Blue

    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    
    # Draw a stylized 'F'
    import PIL.ImageFont as ImageFont
    try:
        # Try to use a system font
        font = ImageFont.truetype("arialbd.ttf", 48)
        dc.text((16, 4), "F", fill=color2, font=font)
    except IOError:
        # Fallback if font isn't accessible: draw 'F' with rectangles
        dc.rectangle([16, 10, 48, 18], fill=color2) # Top crossbar
        dc.rectangle([16, 10, 24, 54], fill=color2) # Vertical stem
        dc.rectangle([16, 28, 40, 36], fill=color2) # Middle crossbar
if __name__ == "__main__":
    with open("friday_debug.log", "a") as f:
        f.write(f"Args: {sys.argv}\n")
    if len(sys.argv) > 1 and sys.argv[1] == "--widget":
        with open("friday_debug.log", "a") as f:
            f.write("Starting widget mode\n")
        import ui_widget
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        app = ui_widget.FridayWidget()
        with open("friday_debug.log", "a") as f:
            f.write("Widget instantiated. Starting mainloop.\n")
        app.mainloop()
        sys.exit(0)

    core = FridayCore()
    
    # Start the listening loop automatically on boot in a background thread
    core.listening_thread = threading.Thread(target=core.start_listening_loop, daemon=True)
    core.listening_thread.start()
    
    # Run the system tray icon (this blocks the main thread, keeping the program alive)
    tray = create_tray_icon(core)
    tray.run()
