import os
import time
import sqlite3
from datetime import datetime
import cv2
from win32com.client import Dispatch
import sys

def speak(str1):
    speak = Dispatch("SAPI.SpVoice")
    speak.Speak(str1)

# Initialize SQLite database
DB_NAME = "attendance_system.db"
CONFIDENCE_THRESHOLD = 55
RECOGNITION_TIME_THRESHOLD = 2  # 2 seconds threshold

def recognize_face():
    # Load the LBPH recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("Trainer.yml")

    # Load the mapping of numerical IDs to usernames
    label_to_name = {}
    with open("label_mapping.txt", "r") as file:
        for line in file:
            label_id, username = line.strip().split(":")
            label_to_name[int(label_id)] = username

    # Initialize the face detector
    facedetect = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    # Start video capture
    video = cv2.VideoCapture(0)
    
    # Variables for tracking recognition time
    recognition_start_time = None
    current_recognition = None
    recognized_name = "Unknown"

    try:
        while True:
            ret, frame = video.read()
            if not ret:
                print("Error accessing the camera.", file=sys.stderr)  # Redirect to stderr
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = facedetect.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                serial, conf = recognizer.predict(gray[y:y + h, x:x + w])

                if conf < CONFIDENCE_THRESHOLD:
                    name = label_to_name.get(serial, "Unknown")
                    color = (0, 255, 0)  # Green for recognized faces
                    
                    if current_recognition != name:
                        current_recognition = name
                        recognition_start_time = time.time()
                    elif recognition_start_time is not None:
                        recognition_duration = time.time() - recognition_start_time
                        if recognition_duration >= RECOGNITION_TIME_THRESHOLD:
                            video.release()
                            cv2.destroyAllWindows()
                            # print(f"DEBUG: Recognition result: {name}")  # Commented out
                            print(name)  # Only the name is printed
                            sys.stdout.flush()  # Ensure immediate output
                            return name
                else:
                    name = "Unknown"
                    color = (0, 0, 255)  # Red for unknown faces
                    
                    if current_recognition != "Unknown":
                        current_recognition = "Unknown"
                        recognition_start_time = time.time()
                    elif recognition_start_time is not None:
                        recognition_duration = time.time() - recognition_start_time
                        if recognition_duration >= RECOGNITION_TIME_THRESHOLD:
                            video.release()
                            cv2.destroyAllWindows()
                            # print(f"DEBUG: Recognition result: {name}")  # Commented out
                            print(name)  # Only "Unknown" is printed
                            sys.stdout.flush()
                            return name

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.rectangle(frame, (x, y - 40), (x + w, y), color, -1)
                cv2.putText(frame, f"{name} ({int(conf)})", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow("Face Recognition", frame)

            if cv2.waitKey(1) == ord("q"):
                break

    except Exception as e:
        sys.stderr.write(f"DEBUG: Error in face recognition: {str(e)}\n")  # Error to stderr
        print("Unknown")  # Only "Unknown" to stdout
        sys.stdout.flush()
    finally:
        video.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    recognize_face()