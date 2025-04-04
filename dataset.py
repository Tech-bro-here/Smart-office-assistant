import cv2
import sys
import os

def generate_dataset(name):
    if not name:
        print("Error: Name cannot be empty")
        return False
        
    # Create data directory if it doesn't exist
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Initialize face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Start video capture
    cap = cv2.VideoCapture(0)
    
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            count += 1
            # Save the captured face
            cv2.imwrite(f"data/{name}.{count}.jpg", gray[y:y+h, x:x+w])
            
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
        cv2.imshow('Capturing Face Data', frame)
        
        # Break if 'q' is pressed or enough samples collected
        if cv2.waitKey(1) == ord('q') or count >= 100:
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python dataset.py <name>")
        sys.exit(1)
    
    success = generate_dataset(sys.argv[1])
    sys.exit(0 if success else 1)