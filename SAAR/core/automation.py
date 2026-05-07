# core/automation.py

import os
import time
import pyautogui
import subprocess
import webbrowser
import pyperclip


# =========================
# BROWSER CONTROL
# =========================

def open_chrome():
    try:
        subprocess.Popen("chrome")
        time.sleep(2)
        return True
    except:
        return False


def go_to_website(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return True


def search_in_browser(query: str):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return True


# =========================
# NOTEPAD CONTROL
# =========================

def open_notepad():
    subprocess.Popen("notepad")
    time.sleep(1.5)


def new_file():
    pyautogui.hotkey("ctrl", "n")
    time.sleep(0.5)


# -------- SAFE WRITE (for code) --------
def write_text_safe(text):
    pyperclip.copy(text)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)


# -------- FAST WRITE (for small text) --------
def write_text_fast(text):
    pyautogui.write(text, interval=0.02)
    time.sleep(0.2)


# -------- AUTO MODE --------
def write_text(text):
    # If code or long text → use safe mode
    if len(text) > 200 or "#include" in text or "int main" in text or "def " in text or "class " in text:
        write_text_safe(text)
    else:
        write_text_fast(text)


def save_file(folder: str, filename: str):
    pyautogui.hotkey("ctrl", "s")
    time.sleep(1)

    full_path = os.path.join(folder, filename)
    pyautogui.write(full_path)
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(0.5)


def create_folder(folder: str):
    if not os.path.exists(folder):
        os.makedirs(folder)


# =========================
# AUTO-TYPING (Phase 2)
# =========================
def auto_type(text: str, delay_before: int = 3):
    """Waits for a few seconds (to switch windows) and then auto-types the given text."""
    try:
        print(f"Auto-typing starting in {delay_before} seconds...")
        time.sleep(delay_before)
        pyautogui.write(text, interval=0.03)
        return "Auto-typing completed boss."
    except Exception as e:
        return f"Auto-typing Error: {e}"

# =========================
# CLOSE APPS
# =========================

def close_app(text: str):
    if "notepad" in text:
        subprocess.call("taskkill /f /im notepad.exe", shell=True)
        return True

    if "chrome" in text:
        subprocess.call("taskkill /f /im chrome.exe", shell=True)
        return True

    return False
