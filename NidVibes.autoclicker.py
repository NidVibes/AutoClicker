import threading
import time
import json
import os
import sys
import tkinter as tk
from tkinter import ttk
import pyautogui
from pynput import keyboard

# Safety settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.001


def get_config_path():
    """Return a writable path for hotkeys.json — works for both script and EXE."""
    if getattr(sys, "frozen", False):
        if os.name == "nt":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
            base = os.path.join(base, "NidAuraAutoClicker")
        else:
            base = os.path.join(os.path.expanduser("~"), ".config", "nidAura_autoclicker")
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        base = os.path.expanduser("~")
    return os.path.join(base, "hotkeys.json")


HOTKEYS_FILE = get_config_path()

DEFAULT_HOTKEYS = {
    "start_pause": "f6",
    "close": "f7",
    "single_click": "f4",
    "double_click": "f5",
    "right_click": "f8",
    "mouse_move": "f9",
}

ACTION_LABELS = {
    "start_pause": "Start / Pause",
    "close": "Close Application",
    "single_click": "Single-Click (one-shot)",
    "double_click": "Double-Click (one-shot)",
    "right_click": "Right-Click (one-shot)",
    "mouse_move": "Toggle Mouse Mover",
}

LICENSE_TEXT = """MIT License

Copyright (c) 2026 NidAura / www.nidvibes.com / https://github.com/NidVibes

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


def key_to_str(key):
    if isinstance(key, keyboard.Key):
        return key.name
    if isinstance(key, keyboard.KeyCode):
        if key.char:
            return key.char.lower()
        if key.vk is not None:
            return f"vk{key.vk}"
    return str(key)


def display_key(key_str):
    if len(key_str) == 1:
        return key_str.upper()
    return key_str.capitalize()


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NidAura Auto-Clicker")
        self.root.geometry("380x720")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")

        self.running = False
        self.program_running = True
        self.mouse_moving = False
        self.mover_speed = 2
        self.cps_value = 20.0

        self.mouse_lock = threading.Lock()

        self.capturing_action = None
        self.settings_window = None
        self.settings_labels = {}
        self.hotkeys = dict(DEFAULT_HOTKEYS)
        self.load_hotkeys()

        # Ensure hotkeys.json exists on disk even on very first launch
        if not os.path.exists(HOTKEYS_FILE):
            self.save_hotkeys()

        self.create_widgets()

        threading.Thread(target=self.clicking_loop, daemon=True).start()
        threading.Thread(target=self.mouse_mover_loop, daemon=True).start()
        threading.Thread(target=self.start_listener, daemon=True).start()

    def create_widgets(self):
        tk.Label(self.root, text="NidAura AUTO-CLICKER",
                 font=("Helvetica", 16, "bold"), fg="#00ffcc", bg="#1e1e1e").pack(pady=(16, 2))
        tk.Label(self.root, text="Created with love by NidAura www.nidAura.com",
                 font=("Helvetica", 10, "italic"), fg="#888888", bg="#1e1e1e").pack(pady=(0, 10))

        status_frame = tk.Frame(self.root, bg="#2d2d2d", padx=10, pady=8, relief="groove", bd=2)
        status_frame.pack(fill="x", padx=20, pady=4)

        self.status_text = tk.Label(status_frame, text="STATUS: IDLE ⏸️",
                                    font=("Helvetica", 11, "bold"), fg="#ff5555", bg="#2d2d2d")
        self.status_text.pack()

        cps_frame = tk.Frame(self.root, bg="#1e1e1e")
        cps_frame.pack(pady=8, padx=20, fill="x")

        tk.Label(cps_frame, text="Clicks Per Second (CPS):",
                 font=("Helvetica", 10, "bold"), fg="#ffffff", bg="#1e1e1e").pack(anchor="w")

        self.cps_slider = ttk.Scale(cps_frame, from_=1, to=50, orient="horizontal",
                                    command=self.update_cps_label)
        self.cps_slider.set(20)
        self.cps_slider.pack(fill="x", pady=4)

        self.cps_val_label = tk.Label(cps_frame, text="20 CPS",
                                      font=("Helvetica", 9), fg="#cccccc", bg="#1e1e1e")
        self.cps_val_label.pack(anchor="e")

        mover_frame = tk.Frame(self.root, bg="#1e1e1e")
        mover_frame.pack(pady=8, padx=20, fill="x")

        mover_header = tk.Frame(mover_frame, bg="#1e1e1e")
        mover_header.pack(fill="x")

        tk.Label(mover_header, text="Mouse Mover:",
                 font=("Helvetica", 10, "bold"), fg="#ffffff", bg="#1e1e1e").pack(side="left")
        self.mover_status_label = tk.Label(mover_header, text="OFF",
                                           font=("Helvetica", 10, "bold"), fg="#ff5555", bg="#1e1e1e")
        self.mover_status_label.pack(side="left", padx=(6, 0))
        self.mover_btn = tk.Button(mover_header, text="Start",
                                   font=("Helvetica", 9), bg="#333333", fg="#00ffcc",
                                   activebackground="#444444", activeforeground="#00ffcc",
                                   relief="flat", command=self.toggle_mouse_mover)
        self.mover_btn.pack(side="right")

        tk.Label(mover_frame, text="Mover Speed:", font=("Helvetica", 9),
                 fg="#cccccc", bg="#1e1e1e").pack(anchor="w", pady=(6, 0))
        self.mover_speed_slider = ttk.Scale(mover_frame, from_=1, to=10, orient="horizontal",
                                            command=self.update_mover_speed)
        self.mover_speed_slider.set(2)
        self.mover_speed_slider.pack(fill="x", pady=2)
        self.mover_speed_label = tk.Label(mover_frame, text="2",
                                          font=("Helvetica", 8), fg="#cccccc", bg="#1e1e1e")
        self.mover_speed_label.pack(anchor="e")

        hotkey_frame = tk.Frame(self.root, bg="#252525", padx=12, pady=8)
        hotkey_frame.pack(fill="x", padx=20, pady=4)

        tk.Label(hotkey_frame, text="HOTKEYS:", font=("Helvetica", 9, "bold"),
                 fg="#00ffcc", bg="#252525").pack(anchor="w")

        self.hotkey_labels = {}
        for action in ["start_pause", "single_click", "double_click", "right_click",
                       "mouse_move", "close"]:
            row = tk.Frame(hotkey_frame, bg="#252525")
            row.pack(fill="x")
            tk.Label(row, text=f"• {ACTION_LABELS[action]}:",
                     font=("Helvetica", 9), fg="#ffffff", bg="#252525").pack(side="left")
            lbl = tk.Label(row, text=display_key(self.hotkeys[action]),
                           font=("Helvetica", 9, "bold"), fg="#00ffcc", bg="#252525")
            lbl.pack(side="left", padx=(4, 0))
            self.hotkey_labels[action] = lbl

        tk.Label(hotkey_frame, text="• SAFETY: Slam mouse to any screen corner",
                 font=("Helvetica", 8, "italic"), fg="#ffaa00", bg="#252525").pack(anchor="w", pady=(4, 0))
        tk.Label(hotkey_frame, text="By using you agree to our License",
                 font=("Helvetica", 8, "italic"), fg="#ffaa00", bg="#252525").pack(anchor="w", pady=(2, 0))

        btn_row = tk.Frame(self.root, bg="#1e1e1e")
        btn_row.pack(pady=8)

        tk.Button(btn_row, text="⚙ Settings", font=("Helvetica", 9),
                  bg="#333333", fg="#00ffcc", activebackground="#444444",
                  activeforeground="#00ffcc", relief="flat",
                  command=self.open_settings).pack(side="left", padx=6)

        tk.Button(btn_row, text="View License", font=("Helvetica", 9),
                  bg="#333333", fg="#00ffcc", activebackground="#444444",
                  activeforeground="#00ffcc", relief="flat",
                  command=self.show_license).pack(side="left", padx=6)

    def show_license(self):
        lic_window = tk.Toplevel(self.root)
        lic_window.title("NidAura AutoClicker License")
        lic_window.geometry("420x350")
        lic_window.resizable(False, False)
        lic_window.configure(bg="#1e1e1e")

        text_frame = tk.Frame(lic_window, bg="#1e1e1e")
        text_frame.pack(fill="both", expand=True, padx=15, pady=15)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        box = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set,
                      bg="#252525", fg="#ffffff", font=("Courier", 9),
                      bd=0, padx=10, pady=10)
        box.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=box.yview)

        box.insert("1.0", LICENSE_TEXT)
        box.config(state="disabled")

    def open_settings(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("Hotkey Settings")
        win.geometry("400x450")
        win.resizable(False, False)
        win.configure(bg="#1e1e1e")
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", lambda: self.close_settings(win))

        self.settings_window = win
        self.settings_labels = {}

        tk.Label(win, text="Configure Hotkeys", font=("Helvetica", 14, "bold"),
                 fg="#00ffcc", bg="#1e1e1e").pack(pady=(15, 4))
        tk.Label(win, text="Click 'Rebind', then press any key (Esc to cancel).",
                 font=("Helvetica", 9, "italic"), fg="#888888", bg="#1e1e1e").pack(pady=(0, 10))

        for action in ["start_pause", "single_click", "double_click", "right_click",
                       "mouse_move", "close"]:
            row = tk.Frame(win, bg="#252525", padx=10, pady=6)
            row.pack(fill="x", padx=20, pady=2)

            tk.Label(row, text=ACTION_LABELS[action], font=("Helvetica", 10),
                     fg="#ffffff", bg="#252525", width=24, anchor="w").pack(side="left")

            lbl = tk.Label(row, text=display_key(self.hotkeys[action]),
                           font=("Helvetica", 10, "bold"), fg="#00ffcc", bg="#252525")
            lbl.pack(side="left", padx=8)

            btn = tk.Button(row, text="Rebind", font=("Helvetica", 9),
                            bg="#333333", fg="#00ffcc", activebackground="#444444",
                            activeforeground="#00ffcc", relief="flat",
                            command=lambda a=action: self.start_capture(a))
            btn.pack(side="right")

            self.settings_labels[action] = lbl

        tk.Button(win, text="Reset to Defaults", font=("Helvetica", 9),
                  bg="#333333", fg="#ffaa00", activebackground="#444444",
                  activeforeground="#ffaa00", relief="flat",
                  command=self.reset_hotkeys).pack(pady=12)

    def close_settings(self, win):
        self.capturing_action = None
        win.destroy()
        self.update_hotkey_labels()

    def reset_hotkeys(self):
        self.hotkeys = dict(DEFAULT_HOTKEYS)
        self.save_hotkeys()
        self.update_hotkey_labels()

    def start_capture(self, action):
        self.capturing_action = action
        if self.settings_window is not None and self.settings_window.winfo_exists():
            for a, lbl in self.settings_labels.items():
                if a == action:
                    lbl.config(text="Press any key... (Esc)", fg="#ffaa00")
                else:
                    lbl.config(text=display_key(self.hotkeys[a]), fg="#00ffcc")

    def finish_capture_str(self, action, key_str):
        if key_str == "esc":
            self.update_hotkey_labels()
            return
        self.hotkeys[action] = key_str
        self.save_hotkeys()
        self.update_hotkey_labels()

    def update_hotkey_labels(self):
        for action, lbl in self.hotkey_labels.items():
            lbl.config(text=display_key(self.hotkeys[action]))
        if self.settings_window is not None and self.settings_window.winfo_exists():
            for action, lbl in self.settings_labels.items():
                lbl.config(text=display_key(self.hotkeys[action]), fg="#00ffcc")

    def load_hotkeys(self):
        try:
            with open(HOTKEYS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in DEFAULT_HOTKEYS:
                if k in data and isinstance(data[k], str) and data[k]:
                    self.hotkeys[k] = data[k]
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

    def save_hotkeys(self):
        try:
            with open(HOTKEYS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.hotkeys, f, indent=2)
        except OSError:
            pass

    def _refresh_status(self):
        if self.running:
            self.status_text.config(text="STATUS: RUNNING 🟢", fg="#55ff55")
        else:
            self.status_text.config(text="STATUS: IDLE ⏸️", fg="#ff5555")

    def _flash_status(self, text, color, duration=500):
        self.status_text.config(text=text, fg=color)
        self.root.after(duration, self._refresh_status)

    def update_cps_label(self, val):
        self.cps_value = max(0.1, float(val))
        self.cps_val_label.config(text=f"{int(self.cps_value)} CPS")

    def update_mover_speed(self, val):
        self.mover_speed = max(1, int(float(val)))
        self.mover_speed_label.config(text=str(self.mover_speed))

    def toggle_clicking(self):
        self.running = not self.running
        self._refresh_status()

    def toggle_mouse_mover(self):
        self.mouse_moving = not self.mouse_moving
        self.update_mover_ui()

    def update_mover_ui(self):
        if self.mouse_moving:
            self.mover_status_label.config(text="ON", fg="#55ff55")
            self.mover_btn.config(text="Stop")
        else:
            self.mover_status_label.config(text="OFF", fg="#ff5555")
            self.mover_btn.config(text="Start")

    def clicking_loop(self):
        while self.program_running:
            if self.running:
                try:
                    with self.mouse_lock:
                        pyautogui.click()
                except pyautogui.FailSafeException:
                    self.running = False
                    self.root.after(0, self._refresh_status)
                    continue
                delay = 1.0 / self.cps_value if self.cps_value > 0 else 0.05
                time.sleep(delay)
            else:
                time.sleep(0.05)

    def mouse_mover_loop(self):
        direction = [1, 1]
        while self.program_running:
            if self.mouse_moving:
                try:
                    with self.mouse_lock:
                        w, h = pyautogui.size()
                        x, y = pyautogui.position()
                        step = self.mover_speed
                        margin = 20
                        nx = x + direction[0] * step
                        ny = y + direction[1] * step

                        if nx < margin:
                            nx = margin
                            direction[0] = 1
                        elif nx > w - margin:
                            nx = w - margin
                            direction[0] = -1

                        if ny < margin:
                            ny = margin
                            direction[1] = 1
                        elif ny > h - margin:
                            ny = h - margin
                            direction[1] = -1

                        pyautogui.moveTo(nx, ny, duration=0)
                except pyautogui.FailSafeException:
                    self.mouse_moving = False
                    self.root.after(0, self.update_mover_ui)
                    continue
                time.sleep(0.03)
            else:
                time.sleep(0.05)

    # ------------------------------------------------------------------
    # One-shot actions
    # ------------------------------------------------------------------
    def do_single_click(self):
        """Exactly one click at the current position — same mechanism as F6."""
        try:
            with self.mouse_lock:
                pyautogui.click()
            self.root.after(0, self._flash_status, "STATUS: SINGLE-CLICK ✓", "#55ffff", 400)
        except pyautogui.FailSafeException:
            pass

    def do_double_click(self):
        """Two clicks at 20 CPS — same mechanism as F6, but just 2 clicks."""
        delay = 1.0 / 20.0
        try:
            with self.mouse_lock:
                pyautogui.click()
                time.sleep(delay)
                pyautogui.click()
            self.root.after(0, self._flash_status, "STATUS: DOUBLE-CLICK ✓", "#55ffff", 400)
        except pyautogui.FailSafeException:
            pass

    def do_right_click(self):
        try:
            with self.mouse_lock:
                pyautogui.click(button="right")
            self.root.after(0, self._flash_status, "STATUS: RIGHT-CLICK ✓", "#55ffff", 400)
        except pyautogui.FailSafeException:
            pass

    # ------------------------------------------------------------------
    # Global listener
    # ------------------------------------------------------------------
    def start_listener(self):
        def on_press(key):
            if self.capturing_action is not None:
                action = self.capturing_action
                self.capturing_action = None
                self.root.after(0, self.finish_capture_str, action, key_to_str(key))
                return

            key_str = key_to_str(key)

            matched = None
            for action, bound in self.hotkeys.items():
                if key_str == bound:
                    matched = action
                    break

            if matched == "start_pause":
                self.root.after(0, self.toggle_clicking)
            elif matched == "single_click":
                threading.Thread(target=self.do_single_click, daemon=True).start()
            elif matched == "double_click":
                threading.Thread(target=self.do_double_click, daemon=True).start()
            elif matched == "right_click":
                threading.Thread(target=self.do_right_click, daemon=True).start()
            elif matched == "mouse_move":
                self.root.after(0, self.toggle_mouse_mover)
            elif matched == "close":
                self.program_running = False
                self.root.after(0, self.root.quit)
                return False

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()