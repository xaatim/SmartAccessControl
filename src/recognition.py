import colorama
import numpy as np
import cv2
from src.saveAlertImage import save_alert_image
import time
from colorama import Fore

colorama.init()
EMBEDDING_THRESHOLD = 0.7
DETECTION_INTERVAL = 15


def load_known_embeddings():
    try:
        # Windows paths
        embeddings_path = "data/hatim_embeddings.npy"
        labels_path = "data/hatim_labels.npy"

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


known_embeddings, known_labels = load_known_embeddings()


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def recognize_face(face_embedding):
    similarities = [
        cosine_similarity(face_embedding, emb)
        for emb in known_embeddings
    ]
    best_match_idx = np.argmax(similarities)
    best_score = similarities[best_match_idx]

    if best_score > EMBEDDING_THRESHOLD:
        return known_labels[best_match_idx], best_score
    return "Unknown", 0


def process_detected_face(frame, face, task_queue, last_alert_time, purpose):

    anomalyDetected = False
    bbox = face.bbox.astype(int)
    label, score = recognize_face(face.embedding)

    color = (0, 255, 0) if label != "Unknown" else (0, 0, 255)

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
        if purpose != "attendence":
            if current_time - last_alert_time > DETECTION_INTERVAL:
                save_alert_image(frame, task_queue)
                return current_time, anomalyDetected, label

    return last_alert_time, anomalyDetected, label
