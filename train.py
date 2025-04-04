import cv2
import numpy as np
from PIL import Image
import os
import sys

def getImageAndLabels(path):
    try:
        # Get all files in the directory
        imagePaths = [os.path.join(path, f) for f in os.listdir(path) 
                     if os.path.isfile(os.path.join(path, f)) and 
                     f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not imagePaths:
            print("No valid image files found in the data directory")
            return [], []

        face_samples = []
        labels = []
        
        for imagePath in imagePaths:
            try:
                # Read image using OpenCV instead of PIL
                img = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
                
                if img is None:
                    print(f"Failed to load image: {imagePath}")
                    continue
                
                # Extract username from filename
                username = os.path.split(imagePath)[-1].split(".")[0]
                
                # Add to training data
                face_samples.append(img)
                labels.append(username)
                
                # Show training progress
                cv2.imshow("Training on Image", img)
                cv2.waitKey(1)
                
            except Exception as e:
                print(f"Error processing image {imagePath}: {str(e)}")
                continue

        return labels, face_samples

    except Exception as e:
        print(f"Error in getImageAndLabels: {str(e)}")
        return [], []

def main():
    try:
        # Create LBPH Face Recognizer
        recognizer = cv2.face.LBPHFaceRecognizer_create()

        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to the dataset folder
        path = os.path.join(current_dir, "data")
        
        if not os.path.exists(path):
            print(f"Data directory not found: {path}")
            return False

        # Extract usernames and face data
        print("Starting training process...")
        labels, face_data = getImageAndLabels(path)

        if not labels or not face_data:
            print("No valid training data found")
            return False

        # Map usernames to numerical IDs
        unique_labels = list(set(labels))
        label_to_id = {label: idx for idx, label in enumerate(unique_labels)}
        ids = [label_to_id[label] for label in labels]

        # Train the recognizer
        print("Training the recognizer...")
        recognizer.train(face_data, np.array(ids))

        # Save the trained model
        model_path = os.path.join(current_dir, "Trainer.yml")
        recognizer.write(model_path)

        # Save the label mapping
        mapping_path = os.path.join(current_dir, "label_mapping.txt")
        with open(mapping_path, "w") as file:
            for username, label_id in label_to_id.items():
                file.write(f"{label_id}:{username}\n")

        cv2.destroyAllWindows()
        print("Training completed successfully!")
        return True

    except Exception as e:
        print(f"Error in training process: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
