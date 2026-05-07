# core/productivity.py
import threading
import time
import datetime
import winsound
import ctypes

class ProductivityManager:
    def __init__(self):
        self.stopwatch_start = None
        self.work_time_start = None
        self.pomodoro_running = False
        self.blocker_running = False
        self.distraction_sites = ["youtube", "facebook", "instagram", "twitter", "reddit", "netflix"]

    def play_alert(self, beeps=3):
        for _ in range(beeps):
            winsound.Beep(1000, 500)
            time.sleep(0.1)

    # ================= TIMERS & ALARMS =================
    def set_alarm(self, time_str: str):
        """Sets an alarm for HH:MM (24-hour format or AM/PM parsed)."""
        try:
            # Basic parsing, expects formats like "14:30" or "02:30 PM"
            now = datetime.datetime.now()
            alarm_time = None
            if "pm" in time_str.lower() or "am" in time_str.lower():
                alarm_time = datetime.datetime.strptime(time_str.strip().upper(), "%I:%M %p").replace(year=now.year, month=now.month, day=now.day)
            else:
                alarm_time = datetime.datetime.strptime(time_str.strip(), "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            
            if alarm_time < now:
                alarm_time += datetime.timedelta(days=1)
                
            delta_seconds = (alarm_time - now).total_seconds()
            
            def alarm_worker():
                time.sleep(delta_seconds)
                print("\n[ALARM] ALARM RINGING! [ALARM]")
                self.play_alert(beeps=5)
                
            threading.Thread(target=alarm_worker, daemon=True).start()
            return f"Alarm set for {time_str} boss."
        except Exception as e:
            return f"Failed to set alarm: {e}. Please use format HH:MM (e.g., 14:30 or 02:30 PM)."

    def start_timer(self, minutes: int):
        def timer_worker():
            time.sleep(minutes * 60)
            print(f"\n[TIMER] {minutes}-minute timer finished!")
            self.play_alert(beeps=3)
            
        threading.Thread(target=timer_worker, daemon=True).start()
        return f"Timer started for {minutes} minutes boss."

    # ================= STOPWATCH =================
    def start_stopwatch(self):
        self.stopwatch_start = time.time()
        return "Stopwatch started boss."

    def stop_stopwatch(self):
        if not self.stopwatch_start:
            return "Stopwatch wasn't running boss."
        elapsed = time.time() - self.stopwatch_start
        self.stopwatch_start = None
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        return f"Stopwatch stopped. Time elapsed: {h}h {m}m {s}s."

    # ================= POMODORO =================
    def start_pomodoro(self):
        if self.pomodoro_running:
            return "Pomodoro is already running boss."
        
        self.pomodoro_running = True
        
        def pomodoro_worker():
            print("\n[POMODORO] Started: 25 minutes of focus work.")
            time.sleep(25 * 60)
            if not self.pomodoro_running: return
            print("\n[POMODORO] Work phase complete! Take a 5-minute break.")
            self.play_alert(beeps=2)
            time.sleep(5 * 60)
            if not self.pomodoro_running: return
            print("\n[POMODORO] Break complete! Back to work.")
            self.play_alert(beeps=3)
            self.pomodoro_running = False

        threading.Thread(target=pomodoro_worker, daemon=True).start()
        return "Pomodoro cycle started: 25 minutes work, 5 minutes break."

    # ================= TRACK WORK TIME =================
    def track_work_time(self, action: str):
        action = action.lower()
        if action == "start":
            self.work_time_start = time.time()
            return "Started tracking your work time boss."
        elif action == "stop":
            if not self.work_time_start:
                return "You weren't tracking any work time boss."
            elapsed = time.time() - self.work_time_start
            self.work_time_start = None
            m, s = divmod(int(elapsed), 60)
            h, m = divmod(m, 60)
            return f"Work tracking stopped. You worked for {h} hours and {m} minutes today."
        return "Say 'start work time' or 'stop work time'."

    # ================= DISTRACTION BLOCKER =================
    def _distraction_loop(self):
        user32 = ctypes.windll.user32
        while self.blocker_running:
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                window_title = buff.value.lower()
                
                if any(site in window_title for site in self.distraction_sites):
                    # Send WM_CLOSE message
                    user32.PostMessageW(hwnd, 0x0010, 0, 0)
                    print(f"\n[FOCUS] SAAR Focus: Closed distracting window ({window_title})")
                    self.play_alert(beeps=1)
            time.sleep(2)

    def toggle_distraction_blocker(self, enable: bool):
        if enable:
            if self.blocker_running:
                return "Distraction blocker is already active boss."
            self.blocker_running = True
            threading.Thread(target=self._distraction_loop, daemon=True).start()
            return "Distraction blocker ACTIVATED. I will close distracting apps while I'm running."
        else:
            self.blocker_running = False
            return "Distraction blocker DEACTIVATED."

    # ================= INVOICE GENERATOR =================
    def generate_invoice(self, client_name: str, amount: str, item: str):
        """Generates a professional HTML invoice and opens it."""
        try:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            invoice_id = f"SAAR-{int(time.time())}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 50px; color: #333; }}
                    .invoice-box {{ max-width: 800px; margin: auto; padding: 30px; border: 1px solid #eee; box-shadow: 0 0 10px rgba(0, 0, 0, 0.15); }}
                    .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #1A237E; padding-bottom: 20px; }}
                    .footer {{ margin-top: 50px; text-align: center; font-size: 12px; color: #777; }}
                    table {{ width: 100%; text-align: left; border-collapse: collapse; margin-top: 30px; }}
                    th {{ background: #1A237E; color: white; padding: 10px; }}
                    td {{ padding: 10px; border-bottom: 1px solid #eee; }}
                </style>
            </head>
            <body>
                <div class="invoice-box">
                    <div class="header">
                        <div><h1>INVOICE</h1><p>ID: {invoice_id}</p></div>
                        <div style="text-align: right;"><h2>SAAR DIGITAL</h2><p>Sagar's Personal Assistant</p></div>
                    </div>
                    <div style="margin-top: 20px;">
                        <p><strong>Billed To:</strong> {client_name}</p>
                        <p><strong>Date:</strong> {date_str}</p>
                    </div>
                    <table>
                        <thead><tr><th>Description</th><th>Amount</th></tr></thead>
                        <tbody><tr><td>{item}</td><td>Rs.{amount}</td></tr></tbody>
                    </table>
                    <div style="text-align: right; margin-top: 20px;"><h2>Total: Rs.{amount}</h2></div>
                    <div class="footer"><p>Thank you for your business! Generated by SAAR Neural Core.</p></div>
                </div>
            </body>
            </html>
            """
            
            file_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', f"Invoice_{invoice_id}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            import webbrowser
            webbrowser.open(file_path)
            return f"[SUCCESS] Invoice for {client_name} generated and saved to your desktop Sagar!"
        except Exception as e:
            return f"Invoice Error: {e}"

# Global instance
prod_mgr = ProductivityManager()
