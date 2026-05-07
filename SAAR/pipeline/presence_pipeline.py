# pipeline/presence_pipeline.py

import cv2
import time
import ctypes
import threading
from core.presence import PresenceManager

try:
    from fer import FER
    FER_AVAILABLE = True
except (ImportError, Exception):
    FER = None
    FER_AVAILABLE = False
    print("[SAAR] FER emotion library not available — emotion detection disabled.")

# Global Presence Toggle (Can be changed via UI)
PRESENCE_ENABLED = False # Set to False by default to save Sagar's battery
global_presence_tracker = None

class PresencePipeline:
    def __init__(self):
        global global_presence_tracker
        global_presence_tracker = self
        self.manager = PresenceManager()
        self.running = False
        self.missing_seconds = 0
        self.max_missing_seconds = 60 # lock if unseen for 60s
        self.latest_frame = None
        self.detector = FER(mtcnn=True) if FER_AVAILABLE else None  # Use MTCNN for higher accuracy
        self.last_emotion_check = 0
        self.state_manager = None # Will be set during pipeline run

    def verify_user_now(self):
        """Called by brain.py. If running, use latest frame. If not, capture one frame now."""
        if self.running and self.latest_frame is not None:
            trusted, user_id, conf = self.manager.is_trusted(self.latest_frame)
            return trusted, "Face verified via Active Stream" if trusted else "Access denied. Face not recognized."
        
        # On-Demand Capture (Saves Battery)
        print("🔋 [SAAR] On-Demand Eye Activation: Opening camera for 1-second check...")
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return False, "Could not open camera for verification."
        
        # Let camera stabilize for a few frames
        for _ in range(5): cap.read()
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return False, "Failed to capture verification frame."
        
        trusted, user_id, conf = self.manager.is_trusted(frame)
        return trusted, "Face verified via On-Demand Scan" if trusted else "Verification failed Sagar."

    def lock_workstation(self):
        print("\n🔒 SAAR: No trusted user detected. Locking workstation...\n")
        ctypes.windll.user32.LockWorkStation()

    def _loop(self):
        # Use DirectShow backend for better stability on Windows
        video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not video_capture.isOpened():
            print("❌ Presence Pipeline: Could not open webcam.")
            return

        print("🛡️ SAAR Presence Tracker started")

        while self.running:
            ret, frame = video_capture.read()
            if not ret:
                time.sleep(1)
                continue

            self.latest_frame = frame.copy()

            trusted, user_id, conf = self.manager.is_trusted(frame)

            if trusted:
                self.missing_seconds = 0
                # BIOLOGICAL SYNC: Check emotion every 3 iterations (~3 seconds)
                if self.last_emotion_check >= 3:
                    self.detect_emotion(frame)
                    self.last_emotion_check = 0
                else:
                    self.last_emotion_check += 1
            else:
                self.missing_seconds += 1
                if self.missing_seconds >= self.max_missing_seconds:
                    self.lock_workstation()
                    # Reset missing counter to avoid spamming lock command
                    self.missing_seconds = 0
                    # Sleep longer after locking to save CPU while locked
                    time.sleep(5)
            
            # Check presence once per second to save CPU
            time.sleep(1)

        video_capture.release()

    def detect_emotion(self, frame):
        if not FER_AVAILABLE or self.detector is None:
            return
        try:
            emotions = self.detector.top_emotion(frame) # Returns (label, score)
            if emotions:
                label, score = emotions
                if self.state_manager:
                    self.state_manager.set_visual_mood(label.title())
        except Exception as e:
            print(f"[SAAR] FER Vision Error: {e}")

    def start(self, state_manager=None):
        self.state_manager = state_manager

        # ⚙️ Global toggle — set PRESENCE_ENABLED = True to re-enable auto-lock
        if not PRESENCE_ENABLED:
            print("[SAAR] Presence tracking is DISABLED. Set PRESENCE_ENABLED=True to re-enable.")
            return

        if not self.running:
            # reload users to catch freshly enrolled faces
            self.manager.load_users()
            if len(self.manager.known_encodings) == 0:
                print("[SAAR] Presence tracking disabled: No faces enrolled. Run 'python scripts/enroll_face.py'.")
                return
                
            self.running = True
            threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False
