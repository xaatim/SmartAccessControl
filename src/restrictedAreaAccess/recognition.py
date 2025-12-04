import colorama
import numpy as np
from insightface.app import FaceAnalysis
import cv2
from saveAlertImage import save_alert_image
import time
DETECTION_INTERVAL = 15  # Seconds between intruder alerts
from colorama import Fore, Back, Style

colorama.init()
EMBEDDING_THRESHOLD = 0.7  # Minimum similarity score for recognition


def load_known_embeddings():
    """Load pre-trained face embeddings and labels"""
    try:
        # Windows paths
        embeddings_path = r"C:\Users\Hatim\Documents\Github\SmartAccessControl\data\hatim_embeddings.npy"
        labels_path = r"C:\Users\Hatim\Documents\Github\SmartAccessControl\data\hatim_labels.npy"
        
        # Linux paths (commented out)
        # embeddings_path = "/home/hatim/Documents/Github/myFyp/Sherlock_Robot_v0.x/Models/face_embeddings.npy"
        # labels_path = "/home/hatim/Documents/Github/myFyp/Sherlock_Robot_v0.x/Models/labels.npy"
        
        embeddings = np.load(embeddings_path)
        labels = np.load(labels_path)
        
        print(Fore.GREEN + "Known embeddings loaded:", embeddings.shape)
        return embeddings, labels
        
    except Exception as e:
        print(Fore.RED + f"Error loading embeddings: {e}")
        raise

# Initialize face analysis and load known faces
known_embeddings, known_labels = load_known_embeddings()


# ==============================================
# Core Recognition Functions
# ==============================================


def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def recognize_face(face_embedding):
    """
    Compare face embedding against known faces
    Returns: (label, similarity_score)
    """
    similarities = [
        cosine_similarity(face_embedding, emb)
        for emb in known_embeddings
    ]
    best_match_idx = np.argmax(similarities)
    best_score = similarities[best_match_idx]
    
    if best_score > EMBEDDING_THRESHOLD:
        return known_labels[best_match_idx], best_score
    return "Unknown", 0

def process_detected_face(frame, face, task_queue, last_alert_time):
    """
    Process a single detected face:
    - Draw bounding box
    - Recognize identity
    - Trigger alerts for unknown faces
    """
    anomalyDetected = False
    bbox = face.bbox.astype(int)
    label,score = recognize_face(face.embedding)
    
    # Set color based on recognition result
    color = (0, 255, 0) if label != "Unknown" else (0, 0, 255)
    
    # Draw bounding box and label
    cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
    cv2.putText(
        frame, 
        f"{label} {score:.2f}", 
        (bbox[0], bbox[1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 
        0.8, 
        color, 
        2
    )

    if label == "Unknown":
        anomalyDetected = True
        current_time = time.time()
        if current_time - last_alert_time > DETECTION_INTERVAL:
            save_alert_image(frame, task_queue)
            return current_time,anomalyDetected  # Update last alert time
            
    return last_alert_time,anomalyDetected
