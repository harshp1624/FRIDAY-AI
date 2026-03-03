import socket
import threading
import json
import tkinter as tk
import customtkinter as ctk
import sys

# Configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
WIDGET_WIDTH = 350
WIDGET_HEIGHT = 100

class FridayWidget(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure Window
        self.title("F.R.I.D.A.Y. Status")
        self.geometry(f"{WIDGET_WIDTH}x{WIDGET_HEIGHT}")
        self.overrideredirect(True) # Remove borders/titlebar
        self.attributes('-topmost', True) # Always on top
        
        # Make transparent background (Windows specific)
        self.attributes('-alpha', 0.85)
        self.config(bg='#0a0a0a')
        
        # Position in bottom right (above taskbar)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_pos = screen_width - WIDGET_WIDTH - 20
        y_pos = screen_height - WIDGET_HEIGHT - 60
        self.geometry(f"+{x_pos}+{y_pos}")
        
        # UI Elements
        self.frame = ctk.CTkFrame(self, fg_color="#121212", corner_radius=15, border_width=1, border_color="#00c8ff")
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Draggable Header (so user can move it if they want)
        self.header_label = ctk.CTkLabel(self.frame, text="F.R.I.D.A.Y. SENSOR", font=("Consolas", 12, "bold"), text_color="#00c8ff")
        self.header_label.pack(pady=(5, 0))
        
        self.header_label.bind("<ButtonPress-1>", self.start_move)
        self.header_label.bind("<B1-Motion>", self.do_move)
        
        self.status_label = ctk.CTkLabel(self.frame, text="Initializing...", font=("Consolas", 16), text_color="white", wraplength=280)
        self.status_label.pack(expand=True, fill="both", pady=5)

        # Start UDP listener directly
        self.listener_thread = threading.Thread(target=self.udp_listener, daemon=True)
        self.listener_thread.start()
        
    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        x = self.winfo_x() + event.x - self._x
        y = self.winfo_y() + event.y - self._y
        self.geometry(f"+{x}+{y}")

    def update_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)
        
        # Make the widget natively flexible based on string length
        base_width = 350
        base_height = 100
        
        # Calculate rough line count (wraplength is 280, approx 40 chars per line)
        approx_lines = (len(text) // 40) + text.count('\n') + 1
        
        # Add extra height dynamically for multi-line thoughts/typing actions
        new_height = max(base_height, 60 + (approx_lines * 25))
        
        # Keep it anchored to bottom right dynamically
        screen_height = self.winfo_screenheight()
        y_pos = screen_height - new_height - 60
        x_pos = self.winfo_screenwidth() - base_width - 20
        
        self.geometry(f"{base_width}x{new_height}+{x_pos}+{y_pos}")

    def udp_listener(self):
        # Listen for UDP messages from the main python app
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        
        # Make it non-blocking so we can close cleanly eventually
        sock.settimeout(1.0)
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                state = message.get("status", "Unknown")
                
                # Update UI thread-safely
                color = "white"
                if "Idle" in state:
                    color = "#aaaaaa"
                elif "Processing" in state or "Thinking" in state:
                    color = "#00c8ff"
                elif "Listening" in state:
                    color = "#00ff00"
                elif "Silent" in state:
                    color = "#ff5555"
                elif "Error" in state:
                    color = "red"
                    
                self.after(0, self.update_status, state, color)
                
            except socket.timeout:
                continue
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Widget Listener Error: {e}")
                
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = FridayWidget()
    app.mainloop()
