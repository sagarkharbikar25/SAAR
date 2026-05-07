# core/presence.py

import cv2
import face_recognition
import numpy as np
from database.db import db

class PresenceManager:
    def __init__(self, tolerance: float = 0.6): # Enhanced for laptop cams
        self.tolerance = tolerance
        self.known_encodings = []
        self.known_user_ids = []
        self.load_users()

    def load_users(self):
        """Load all faces from DB into memory for quick checking"""
        users = db.fetchall("SELECT id, face_embedding FROM users WHERE face_embedding IS NOT NULL")
        self.known_encodings.clear()
        self.known_user_ids.clear()
        for user in users:
            embedding_list = [float(x) for x in user["face_embedding"].split(",")]
            self.known_encodings.append(np.array(embedding_list))
            self.known_user_ids.append(user["id"])

    def identify_user(self, current_encoding):
        """Compare face encoding to DB users"""
        if not self.known_encodings:
            return None, 0.0

        matches = face_recognition.compare_faces(self.known_encodings, current_encoding, tolerance=self.tolerance)
        face_distances = face_recognition.face_distance(self.known_encodings, current_encoding)
        
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                return self.known_user_ids[best_match_index], (1.0 - face_distances[best_match_index])
        
        return None, 0.0

    def is_trusted(self, frame):
        """Check if any trusted face is in the provided BGR image frame"""
        if not self.known_encodings:
            return False, None, 0.0

        from PIL import Image
        cv_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(cv_rgb).convert('RGB')
        rgb_frame = np.array(pil_img)
        
        # Fast processing: scale down frame to 1/2 size for weak webcams
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)
        
        face_locations = face_recognition.face_locations(small_frame)
        if not face_locations:
            return False, None, 0.0
            
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)
        
        for encoding in face_encodings:
            user_id, confidence = self.identify_user(encoding)
            if user_id:
                return True, user_id, confidence
                
        return False, None, 0.0

    def detect_emotion(self, frame):
        """Analyze the frame for the dominant facial emotion."""
        try:
            from fer import FER
            detector = FER(mtcnn=True) # mtcnn is more accurate for laptop cams
            result = detector.detect_emotions(frame)
            
            if result:
                # Get the first face detected
                emotions = result[0]["emotions"]
                dominant_emotion = max(emotions, key=emotions.get)
                return dominant_emotion
            return "Neutral"
        except Exception as e:
            print(f"[ERROR] FER Error: {e}")
            return "Neutral"
