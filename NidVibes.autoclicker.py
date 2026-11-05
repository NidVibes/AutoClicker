import threading
import time
import tkinter as tk
from tkinter import ttk
import pyautogui
from pynput import keyboard

# Safety settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Elite Auto-Clicker")
        self.root.geometry("380x480")  # Slightly taller to fit the button
        self.root.resizable(False, False)
        
        # Dark Mode Styling
        self.root.configure(bg="#1e1e1e")
        
        self.running = False
        self.program_running = True
        
        # Build UI Elements
        self.create_widgets()
        
        # Start background threads
        threading.Thread(target=self.clicking_loop, daemon=True).start()
        threading.Thread(target=self.start_listener, daemon=True).start()

    def create_widgets(self):
        # Title / Branding
        tk.Label(self.root, text="⚡ PRO AUTO-CLICKER", font=("Helvetica", 16, "bold"), fg="#00ffcc", bg="#1e1e1e").pack(pady=(20, 2))
        
        # <-- PUT YOUR NAME HERE -->
        tk.Label(self.root, text="Created by Your Name Here", font=("Helvetica", 9, "italic"), fg="#888888", bg="#1e1e1e").pack(pady=(0, 15))
        
        # Status Box
        status_frame = tk.Frame(self.root, bg="#2d2d2d", padx=10, pady=10, relief="groove", bd=2)
        status_frame.pack(fill="x", padx=20, pady=5)
        
        self.status_text = tk.Label(status_frame, text="STATUS: IDLE ⏸️", font=("Helvetica", 11, "bold"), fg="#ff5555", bg="#2d2d2d")
        self.status_text.pack()

        # CPS Slider Frame
        cps_frame = tk.Frame(self.root, bg="#1e1e1e")
        cps_frame.pack(pady=15, padx=20, fill="x")
        
        tk.Label(cps_frame, text="Clicks Per Second (CPS):", font=("Helvetica", 10, "bold"), fg="#ffffff", bg="#1e1e1e").pack(anchor="w")
        
        self.cps_slider = ttk.Scale(cps_frame, from_=1, to=50, orient="horizontal", command=self.update_cps_label)
        self.cps_slider.set(20)
        self.cps_slider.pack(fill="x", pady=5)
        
        self.cps_val_label = tk.Label(cps_frame, text="20 CPS", font=("Helvetica", 9), fg="#cccccc", bg="#1e1e1e")
        self.cps_val_label.pack(anchor="e")

        # Instructions Box
        inst_frame = tk.Frame(self.root, bg="#252525", padx=12, pady=10)
        inst_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(inst_frame, text="CONTROLS:", font=("Helvetica", 9, "bold"), fg="#00ffcc", bg="#252525").pack(anchor="w")
        tk.Label(inst_frame, text="• Press [ F6 ] to START / PAUSE clicking", font=("Helvetica", 9), fg="#ffffff", bg="#252525").pack(anchor="w")
        tk.Label(inst_frame, text="• Press [ F7 ] to CLOSE application", font=("Helvetica", 9), fg="#ffffff", bg="#252525").pack(anchor="w")
        tk.Label(inst_frame, text="• SAFETY: Slam mouse to any screen corner", font=("Helvetica", 8, "italic"), fg="#ffaa00", bg="#252525").pack(anchor="w", pady=(4,0))
        tk.Label(inst_frame, text="By using you agree to our License", font=("Helvetica", 8, "italic"), fg="#ffaa00", bg="#252525").pack(anchor="w", pady=(4,0))

        # License Button
        license_btn = tk.Button(self.root, text="View License", font=("Helvetica", 9), bg="#333333", fg="#00ffcc", activebackground="#444444", activeforeground="#00ffcc", relief="flat", command=self.show_license)
        license_btn.pack(pady=10)

    def show_license(self):
        # Create a popup window for the license
        lic_window = tk.Toplevel(self.root)
        lic_window.title("NidVibes AutoClicker License")
        lic_window.geometry("420x350")
        lic_window.resizable(False, False)
        lic_window.configure(bg="#1e1e1e")
        
        # Text area with scrollbar
        text_frame = tk.Frame(lic_window, bg="#1e1e1e")
        text_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        license_text_box = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, bg="#252525", fg="#ffffff", font=("Courier", 9), bd=0, padx=10, pady=10)
        license_text_box.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=license_text_box.yview)
        
        mit_content = """MIT License

Copyright (c) 2026 NidVibes / www.nidvibes.com / https://github.com/NidVibes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TITLE, OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
        
        license_text_box.insert("1.0", mit_content)
        license_text_box.config(state="disabled")  # Make it read-only

    def update_cps_label(self, val):
        cps = float(val)
        self.cps_val_label.config(text=f"{int(cps)} CPS")

    def get_delay(self):
        cps = float(self.cps_slider.get())
        return 1.0 / cps if cps > 0 else 0.05

    def toggle_clicking(self):
        self.running = not self.running
        if self.running:
            self.status_text.config(text="STATUS: RUNNING 🟢", fg="#55ff55")
        else:
            self.status_text.config(text="STATUS: IDLE ⏸️", fg="#ff5555")

    def clicking_loop(self):
        while self.program_running:
            if self.running:
                pyautogui.click()
                time.sleep(self.get_delay())
            else:
                time.sleep(0.05)

    def start_listener(self):
        def on_press(key):
            if key == keyboard.Key.f6:
                self.root.after(0, self.toggle_clicking)
            elif key == keyboard.Key.f7:
                self.program_running = False
                self.root.after(0, self.root.quit)
                return False

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()