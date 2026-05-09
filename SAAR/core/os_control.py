import subprocess
import webbrowser
import os
import time
import pyautogui

import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

APP_ALIASES = {
    "chrome": ["chrome", "google chrome", "browser", "chrom", "crome", "chromuim"],
    "notepad": ["notepad", "note pad", "editor", "writing"],
    "calculator": ["calculator", "calc", "math"],
    "vscode": ["vs code", "vscode", "visual studio", "code"],
    "spotify": ["spotify", "music", "songs"],
    "whatsapp": ["whatsapp", "whats app", "wa app"],
}

# -------------------------
# APP MATCHING
# -------------------------
def _match_app(text: str):
    text = text.lower()
    for app, aliases in APP_ALIASES.items():
        for word in aliases:
            if word in text:
                return app
    return None


# -------------------------
# DYNAMIC APP MATCHING
# -------------------------
import glob
from difflib import get_close_matches

installed_apps_cache = None

def get_all_installed_apps():
    apps = {}
    paths = [
        os.path.join(os.environ.get('APPDATA', ''), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get('PROGRAMDATA', ''), r"Microsoft\Windows\Start Menu\Programs")
    ]
    
    for base_path in paths:
        if not os.path.exists(base_path):
            continue
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".lnk"):
                    app_name = os.path.splitext(file)[0].lower()
                    app_path = os.path.join(root, file)
                    apps[app_name] = app_path
    return apps

def _match_dynamic_app(text: str):
    global installed_apps_cache
    if installed_apps_cache is None:
        installed_apps_cache = get_all_installed_apps()
    
    text = text.lower().replace("open", "").replace("saar", "").strip()
    
    # 1. Direct substring match
    for app_name, app_path in installed_apps_cache.items():
        if text in app_name or app_name in text:
            return app_path
            
    # 2. Fuzzy match
    matches = get_close_matches(text, installed_apps_cache.keys(), n=1, cutoff=0.6)
    if matches:
        return installed_apps_cache[matches[0]]
        
    return None


# -------------------------
# OPEN APPS
# -------------------------
def open_app(text: str):
    app = _match_app(text)
    
    # 1. Static Aliases
    if app:
        try:
            if app == "chrome": 
                try:
                    subprocess.Popen("start chrome", shell=True)
                except:
                    webbrowser.open("https://www.google.com")
            elif app == "notepad": subprocess.Popen("notepad", shell=True)
            elif app == "calculator": subprocess.Popen("calc", shell=True)
            elif app == "vscode": subprocess.Popen("code", shell=True)
            elif app == "whatsapp":
                try:
                    # Try native Windows URI (works if WhatsApp Desktop is installed)
                    subprocess.Popen("start whatsapp://", shell=True)
                except Exception:
                    # Fallback: dynamic Start Menu scan handled below
                    pass
            elif app == "spotify": 
                # Use URI scheme for Windows Store/Native Spotify
                subprocess.Popen("start spotify:", shell=True)
                return app
            return app
        except Exception as e:
            print("[ERROR] Open app error:", e)
            return False

    # 2. Dynamic Start Menu Scan
    app_path = _match_dynamic_app(text)
    if app_path:
        try:
            os.startfile(app_path)
            return os.path.splitext(os.path.basename(app_path))[0]
        except Exception as e:
            print("[ERROR] Dynamic open app error:", e)
            return False
            
    return False


# -------------------------
# CLOSE APPS
# -------------------------
def close_app(text: str) -> bool:
    app = _match_app(text)
    if not app:
        return False

    try:
        if app == "chrome":
            subprocess.run("taskkill /f /im chrome.exe", shell=True)
        elif app == "notepad":
            subprocess.run("taskkill /f /im notepad.exe", shell=True)
        elif app == "calculator":
            subprocess.run("taskkill /f /im calculator.exe", shell=True)
        elif app == "vscode":
            subprocess.run("taskkill /f /im code.exe", shell=True)
        elif app == "whatsapp":
            subprocess.run("taskkill /f /im WhatsApp.exe", shell=True)

        return True

    except Exception as e:
        print("[ERROR] Close app error:", e)
        return False


# -------------------------
# 🌐 WEB AUTOMATION
# -------------------------
def open_youtube():
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube..."


def search_youtube(query: str):
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching YouTube for {query}"


def play_first_video():
    time.sleep(5)  # wait for page to load
    pyautogui.press("tab", presses=6)
    pyautogui.press("enter")
    return "Playing first video."


def pause_or_resume_video():
    pyautogui.press("space")
    return "Toggled play or pause."


def fullscreen_video():
    pyautogui.press("f")
    return "Fullscreen enabled."


def close_youtube():
    subprocess.run("taskkill /f /im chrome.exe", shell=True)
    return "Closed YouTube."


def open_gmail():
    webbrowser.open("https://mail.google.com")
    return "Opening Gmail..."


def search_in_chrome(query: str):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching for {query}"


# -------------------------
# WINDOWS UPDATE
# -------------------------
def update_pc():
    subprocess.Popen("start ms-settings:windowsupdate", shell=True)
    return "Opening Windows update settings"


# -------------------------
# FILE DELETE
# -------------------------
def delete_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"Deleted file {file_path}"
        else:
            return "File not found"
    except Exception as e:
        return f"Error deleting file: {e}"
# -------------------------
# 🔊 SYSTEM CONTROL BRIDGE
# -------------------------
from core.system_control import system_ctrl

def set_volume(level: int):
    return system_ctrl.set_volume(level)

def adjust_volume(delta: int):
    return system_ctrl.change_volume(delta)

def media_key(action: str):
    return system_ctrl.media_control(action)

def check_for_system_updates():
    try:
        # Simple PowerShell check for pending updates
        cmd = 'powershell -Command "Get-WindowsUpdate -IsInstalled 0"' # Requires PSWindowsUpdate module often, or use basic check
        # More compatible check:
        cmd = 'powershell -Command "$updateSession = New-Object -ComObject Microsoft.Update.Session; $updateSearcher = $updateSession.CreateUpdateSearcher(); $searchResult = $updateSearcher.Search(\'IsInstalled=0\'); if ($searchResult.Updates.Count -gt 0) { echo \"Pending Updates: $($searchResult.Updates.Count)\" } else { echo \"No updates pending\" }"'
        import subprocess
        result = subprocess.check_output(cmd, shell=True).decode().strip()
        return result if result else "System is up to date boss."
    except Exception as e:
        return f"Update Check Error: {e}"

# -------------------------
# 🛠️ PHASE 1: CORE OS ENGINE
# -------------------------
import ctypes
import psutil
from datetime import datetime

try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None
try:
    import winshell
except ImportError:
    winshell = None

def set_brightness(level: int):
    if sbc:
        try:
            sbc.set_brightness(level)
            return f"Screen brightness set to {level}%"
        except Exception as e:
            return f"Failed to set brightness: {e}"
    return "Brightness control module not installed."

def lock_screen():
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked."
    except Exception as e:
        return f"Failed to lock screen: {e}"

def set_mouse_speed(speed: int):
    # Windows mouse speed is 1 (slow) to 20 (fast), default 10
    speed = max(1, min(20, speed))
    try:
        # SPI_SETMOUSESPEED = 113
        ctypes.windll.user32.SystemParametersInfoW(113, 0, speed, 0)
        return f"Mouse speed set to {speed}."
    except Exception as e:
        return f"Failed to set mouse speed: {e}"

def empty_recycle_bin():
    if winshell:
        try:
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            return "Recycle bin emptied."
        except Exception as e:
            return f"Failed to empty recycle bin: {e}"
    return "winshell module not installed."

def take_screenshot():
    try:
        # Save to desktop
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        filename = os.path.join(desktop, f"screenshot_{int(time.time())}.png")
        pyautogui.screenshot(filename)
        return f"Screenshot saved to desktop as {os.path.basename(filename)}"
    except Exception as e:
        return f"Failed to take screenshot: {e}"

def open_task_manager():
    subprocess.Popen("taskmgr", shell=True)
    return "Opened Task Manager."

def run_virus_scan():
    try:
        cmd = r'"%ProgramFiles%\Windows Defender\MpCmdRun.exe" -Scan -ScanType 1'
        subprocess.Popen(cmd, shell=True)
        return "Started Windows Defender Quick Scan in background."
    except Exception as e:
        return f"Failed to start virus scan: {e}"

def run_disk_cleaner():
    try:
        subprocess.Popen("cleanmgr /sagerun:1", shell=True)
        return "Started Disk Cleaner."
    except Exception as e:
        return f"Failed to start disk cleaner: {e}"

def check_pc_temp():
    try:
        import wmi
        w = wmi.WMI(namespace="root\\wmi")
        temp = w.MSAcpi_ThermalZoneTemperature()[0]
        # Temperature is in tenths of degrees Kelvin
        celsius = (temp.CurrentTemperature / 10.0) - 273.15
        return f"Current PC Temperature is roughly {celsius:.1f} deg C."
    except Exception:
        return "PC Temperature reading requires Administrator privileges."

def check_network_speed():
    try:
        net_io_1 = psutil.net_io_counters()
        time.sleep(1)
        net_io_2 = psutil.net_io_counters()
        
        down_speed = (net_io_2.bytes_recv - net_io_1.bytes_recv) / 1024 / 1024 # MB/s
        up_speed = (net_io_2.bytes_sent - net_io_1.bytes_sent) / 1024 / 1024 # MB/s
        
        return f"Network Speed: {down_speed:.2f} MB/s Download, {up_speed:.2f} MB/s Upload."
    except Exception as e:
        return f"Failed to check network speed: {e}"

def terminate_saar():
    """Gracefully closes the SAAR application."""
    print("[SYSTEM] [Neural Terminate] Initiating shutdown sequence...")
    # Give a tiny delay for the voice to finish if possible, then exit
    os._exit(0)

def power_manager(action: str):
    """Shutdown, restart, sleep, or hibernate the PC."""
    action = action.lower()
    
    # SAFETY: If 'saar' is in the command, we assume they mean the app, not the PC
    if "saar" in action and "shutdown" in action:
        return "TERMINATE_SAAR" # Special token for the brain to handle

    try:
        if "shutdown" in action or "turn off" in action or "power off" in action:
            # Require 'pc' or 'laptop' to be sure
            if any(w in action for w in ["pc", "laptop", "computer", "system", "windows"]):
                subprocess.run("shutdown /s /t 10", shell=True)
                return "Shutting down your PC in 10 seconds Sagar. Say 'cancel shutdown' to abort."
            else:
                return "Do you want to shutdown your PC or just close SAAR, Sagar?"
                
        elif "restart" in action or "reboot" in action:
            subprocess.run("shutdown /r /t 10", shell=True)
            return "Restarting in 10 seconds Sagar. Say 'cancel restart' to abort."
        elif "sleep" in action:
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
            return "Going to sleep Sagar."
        elif "hibernate" in action:
            subprocess.run("shutdown /h", shell=True)
            return "Hibernating Sagar."
        elif "cancel" in action:
            subprocess.run("shutdown /a", shell=True)
            return "Shutdown/restart cancelled Sagar."
        else:
            return "Tell me what to do Sagar: shutdown pc, restart, sleep, or hibernate."
    except Exception as e:
        return f"Power Manager Error: {e}"


def toggle_mic(mute: bool = True):
    """Mute or unmute the default microphone using PowerShell."""
    try:
        action = "Mute" if mute else "Unmute"
        # Uses SoundVolumeView or PowerShell Audio API approach
        cmd = f'powershell -Command "$obj = New-Object -ComObject SAPI.SpVoice; $obj.AudioInput"'
        # More reliable: use nircmd if available, fallback to settings
        try:
            if mute:
                subprocess.Popen("nircmd mutesysvolume 1 microphone", shell=True)
            else:
                subprocess.Popen("nircmd mutesysvolume 0 microphone", shell=True)
            return f"Microphone {'muted' if mute else 'unmuted'} boss."
        except Exception:
            # Fallback: open Sound settings
            subprocess.Popen("start ms-settings:sound", shell=True)
            return f"Opened Sound settings to {action.lower()} microphone manually boss."
    except Exception as e:
        return f"Mic Control Error: {e}"


def start_screen_record():
    """Start Windows Game Bar screen recording (Win+Alt+R)."""
    try:
        import pyautogui
        pyautogui.hotkey('win', 'alt', 'r')
        return "Screen recording started boss! Press Win+Alt+R again to stop."
    except Exception as e:
        return f"Screen Record Error: {e}"


def stop_screen_record():
    """Stop Windows Game Bar screen recording."""
    try:
        import pyautogui
        pyautogui.hotkey('win', 'alt', 'r')
        return "Screen recording stopped boss! Check your Videos/Captures folder."
    except Exception as e:
        return f"Screen Record Stop Error: {e}"


def open_settings_hub(target: str):
    targets = {
        "wifi": "ms-settings:network-wifi",
        "bluetooth": "ms-settings:bluetooth",
        "printer": "ms-settings:printers",
        "battery": "ms-settings:batterysaver",
        "nightmode": "ms-settings:nightlight",
        "webcam": "ms-settings:privacy-webcam"
    }
    target = target.lower()
    if target in targets:
        subprocess.Popen(f"start {targets[target]}", shell=True)
        return f"Opened {target} settings."
    return "Unknown settings target."

# =========================
# THE FINAL 5 FEATURES
# =========================

def update_system_apps():
    """Run winget upgrade --all in the background."""
    try:
        subprocess.Popen("start cmd /k winget upgrade --all --accept-package-agreements --accept-source-agreements", shell=True)
        return "Updating all your system apps in the background, Sagar. This might take a few minutes."
    except Exception as e:
        return f"Failed to start Winget updater: {e}"

def change_wallpaper():
    """Change the Windows wallpaper to a random image in the Pictures folder."""
    import ctypes
    import random
    import glob
    
    pictures_folder = os.path.join(os.environ["USERPROFILE"], "Pictures")
    images = glob.glob(os.path.join(pictures_folder, "*.jpg")) + glob.glob(os.path.join(pictures_folder, "*.png"))
    
    if not images:
        return "I couldn't find any pictures in your Pictures folder to set as wallpaper."
        
    random_image = random.choice(images)
    try:
        # SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(20, 0, random_image, 3)
        return "Wallpaper changed successfully, boss!"
    except Exception as e:
        return f"Failed to change wallpaper: {e}"

def move_window_to_monitor():
    """Uses Win + Shift + Right to move active window to the next monitor."""
    try:
        import pyautogui
        pyautogui.hotkey('win', 'shift', 'right')
        return "Window moved to the adjacent monitor."
    except Exception as e:
        return f"Failed to move window: {e}"

def refresh_desktop():
    """Refreshes the Windows desktop to show new files."""
    try:
        import ctypes
        # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        return "Desktop refreshed boss!"
    except Exception as e:
        return f"Refresh Error: {e}"

def pin_window_to_top():
    """Pins the currently active window to be always on top."""
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        if win:
            # We use a shortcut or a library if available, but pygetwindow doesn't support 'always on top' directly easily.
            # Fallback: use a simple pyautogui sequence or advise user.
            return "To pin a window, please use 'Win + Ctrl + T' if you have PowerToys, or I can try a custom script Sagar."
        return "No active window found."
    except Exception as e:
        return f"Pin Error: {e}"

def create_quick_note(content: str):
    """Saves a quick note to the desktop."""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        note_path = os.path.join(desktop, "SAAR_Quick_Note.txt")
        with open(note_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {content}")
        return "Quick note saved to your desktop Sagar!"
    except Exception as e:
        return f"Note Error: {e}"

def copy_file_path(file_path: str):
    """Copies the full path of a file to the clipboard."""
    try:
        import pyperclip
        pyperclip.copy(file_path)
        return f"Full path of {os.path.basename(file_path)} copied to clipboard Sagar!"
    except Exception as e:
        return f"Copy Path Error: {e}"

# --- Clipboard History Thread ---
CLIPBOARD_HISTORY = []
def _clipboard_monitor():
    import pyperclip
    last_clipboard = ""
    while True:
        try:
            current = pyperclip.paste()
            if current and current != last_clipboard and len(current.strip()) > 0:
                last_clipboard = current
                if current not in CLIPBOARD_HISTORY:
                    CLIPBOARD_HISTORY.insert(0, current)
                    if len(CLIPBOARD_HISTORY) > 5:
                        CLIPBOARD_HISTORY.pop()
        except:
            pass
        time.sleep(2)

import threading
clipboard_thread = threading.Thread(target=_clipboard_monitor, daemon=True)
clipboard_thread.start()

def get_clipboard_history():
    if not CLIPBOARD_HISTORY:
        return "I haven't seen you copy anything recently, my friend. Your clipboard is empty right now!"
    
    hist = "\n".join([f"{i+1}. {txt[:50]}..." if len(txt) > 50 else f"{i+1}. {txt}" for i, txt in enumerate(CLIPBOARD_HISTORY)])
    return f"Sure thing! Here is what you've copied recently:\n{hist}"
