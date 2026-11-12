 NidAura Auto-Clicker 

A lightweight, modern desktop auto-clicker built with Python, Tkinter, PyAutoGUI, and Pynput. 

Features a customizable CPS slider, rebindable hotkeys, a built-in mouse mover, and a dark-mode UI with global controls that work while the window is unfocused.

Features

- Customizable CPS: Adjust clicking speed dynamically from 1 to 50 Clicks Per Second.
- Global Hotkeys:
  - `F4`: Single-click (one-shot)
  - `F5`: Double-click (one-shot)
  - `F6`: Toggle Start / Pause auto-clicking
  - `F7`: Close application
  - `F8`: Right-click (one-shot)
  - `F9`: Toggle Mouse Mover
- Rebindable Hotkeys: All bindings can be reassigned via the ⚙ Settings window and persist in `hotkeys.json`.
- Mouse Mover: Slowly drifts the cursor within screen bounds. Speed adjustable from 1 to 10.
- Safety First: Built-in `pyautogui` fail-safe — slam the mouse into any screen corner to abort.
- Dark Mode UI: Tkinter with background threads so the interface never freezes.



Installation & Setup

 Prerequisites
Make sure you have [Python 3.x](https://www.python.org/) installed.

 1. Clone the repository

```bash
git clone https://github.com/NidVibes/AutoClicker.git
cd AutoClicker