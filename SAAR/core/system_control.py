# core/system_control.py
import os
import ctypes
import pyautogui

try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except Exception:
    PYCAW_AVAILABLE = False

class SystemController:
    def __init__(self):
        pass  # Lazy init — don't grab audio at import time

    def _get_volume_interface(self):
        """Grab a fresh audio interface every time (avoids stale None)."""
        if not PYCAW_AVAILABLE:
            return None
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
            return volume
        except Exception:
            return None

    def set_volume(self, level: int):
        """Level: 0 to 100"""
        vol = self._get_volume_interface()
        if not vol:
            # Fallback: use pyautogui volume keys
            return "Volume control unavailable — use keyboard volume keys boss."
        vol.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level}%"

    def change_volume(self, delta: int):
        vol = self._get_volume_interface()
        if not vol:
            # Fallback: press volume key the right number of times
            key = "volumeup" if delta > 0 else "volumedown"
            presses = abs(delta) // 2  # Each press ~ 2%
            pyautogui.press(key, presses=max(1, presses))
            direction = "up" if delta > 0 else "down"
            return f"Volume adjusted {direction} boss."
        current = vol.GetMasterVolumeLevelScalar()
        new_vol = min(1.0, max(0.0, current + (delta / 100)))
        vol.SetMasterVolumeLevelScalar(new_vol, None)
        return f"Volume adjusted to {int(new_vol * 100)}%"

    def mute(self, state: bool):
        vol = self._get_volume_interface()
        if not vol:
            pyautogui.press("volumemute")
            return "System Muted" if state else "System Unmuted"
        vol.SetMute(1 if state else 0, None)
        return "System Muted" if state else "System Unmuted"

    def media_control(self, action: str):
        actions = {
            "pause": "playpause",
            "resume": "playpause",
            "next": "nexttrack",
            "previous": "prevtrack",
            "stop": "stop",
            "mute": "volumemute"
        }
        if action in actions:
            pyautogui.press(actions[action])
            return f"Media {action}."
        return "Invalid media action boss."

    def focus_mode(self):
        pyautogui.hotkey('win', 'd')
        return "Focus mode enabled. Background noise cleared."

# Global Instance
system_ctrl = SystemController()
