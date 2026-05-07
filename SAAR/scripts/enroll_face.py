import cv2
import face_recognition
import sys
import os

# Add parent directory to path to import database module
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

try:
    from database.db import db
except ImportError:
    print("[ERROR] Could not find the SAAR database module. Make sure you are running this from the SAAR folder.")
    sys.exit(1)

def enroll_face(name: str):
    print(f"[CAM] Creating face profile for {name}...")
    print("!!! IMPORTANT: Close the main SAAR app before running this to free the webcam !!!")
    print("Please look directly at the webcam. Press 's' to capture your face or 'q' to quit.")
    
    # Use standard index
    video_capture = cv2.VideoCapture(0)
    
    if not video_capture.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("[ERROR] Failed to grab frame.")
            break
            
        cv2.imshow("Enroll Face - Press 's' to Save", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            print("Processing face... Please hold still.")
            import numpy as np
            from PIL import Image
            
            # Convert to PIL Image and force 'RGB' mode to guarantee 8-bit 3-channel
            cv_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(cv_rgb).convert('RGB')
            rgb_frame = np.array(pil_img)
            
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if len(face_locations) == 0:
                print("[-] No face found! Please try again and make sure your room is well lit.")
            elif len(face_locations) > 1:
                print("[-] Multiple faces found! Please ensure only you are in the frame.")
            else:
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if face_encodings:
                    encoding = face_encodings[0]
                    # Convert embedding to string for database
                    embedding_str = ",".join(str(x) for x in encoding)
                    
                    # Store in database
                    db.execute(
                        "INSERT INTO users (name, language, face_embedding) VALUES (?, ?, ?)",
                        (name, "English", embedding_str)
                    )
                    
                    print(f"[+] Successfully enrolled {name}'s face into SAAR!")
                    break
        elif key == ord('q'):
            print("Exiting without saving.")
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    enroll_face("Sagar")
