# core/reminders.py
import os
import json
import time
import threading
from datetime import datetime, timedelta
import dateparser

from voice.tts import speak
from core.os_control import media_key

REMINDERS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "reminders.json"
)

class ReminderSystem:
    def __init__(self):
        self.reminders = self._load()
        self._start_daemon()

    def _load(self):
        if not os.path.exists(REMINDERS_FILE):
            self._save([])
            return []
        with open(REMINDERS_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []

    def _save(self, data):
        with open(REMINDERS_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def add_reminder(self, task: str, time_str: str):
        # Handle simple relative times like "in 10 minutes"
        if time_str.startswith("in "):
            parsed_time = dateparser.parse(time_str)
        else:
            # Handle absolute times like "at 5 PM"
            parsed_time = dateparser.parse(time_str.replace("at ", ""))
            
        if not parsed_time:
            return "[ERROR] Sorry Sagar, I couldn't understand that time format."

        # If it's an absolute time that has already passed today, assume tomorrow
        if parsed_time < datetime.now():
            parsed_time += timedelta(days=1)

        reminder = {
            "task": task.strip(),
            "time": parsed_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.reminders.append(reminder)
        self._save(self.reminders)
        
        friendly_time = parsed_time.strftime("%I:%M %p")
        return f"[SUCCESS] Reminder set! I'll remind you to {task} at {friendly_time}."

    def _start_daemon(self):
        def loop():
            while True:
                now = datetime.now()
                pending = []
                triggered = []
                
                for r in self.reminders:
                    try:
                        t = datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S")
                        if now >= t:
                            triggered.append(r)
                        else:
                            pending.append(r)
                    except:
                        pass # Ignore malformed

                if triggered:
                    self.reminders = pending
                    self._save(self.reminders)
                    for r in triggered:
                        print(f"\n[REMINDER ALERT] {r['task']}")
                        speak(f"Reminder for you Sagar: {r['task']}")
                        # Pause a bit between multiple reminders
                        time.sleep(2)
                
                time.sleep(10) # Check every 10 seconds

        t = threading.Thread(target=loop, daemon=True)
        t.start()

# Global instance
reminders = ReminderSystem()
