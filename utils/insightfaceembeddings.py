import os
import numpy as np
import cv2
from insightface.app import FaceAnalysis

# Directory with images
IMAGE_DIR = r"/home/hatim/Documents/Github/SmartAccessControl/data/images"  # Change this to your folder
LABEL_NAME = "Hatim"       # Change label as needed

# Initialize InsightFace
app = FaceAnalysis(name='antelopev2' ,allowed_modules=['detection', 'recognition', ])
app.prepare(ctx_id=-1)  # CPU

embeddings = []
labels = []

# Loop over all images in folder
for filename in os.listdir(IMAGE_DIR):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(IMAGE_DIR, filename)
        img = cv2.imread(img_path)

        if img is None:
            print(f"❌ Could not read {img_path}")
            continue

        faces = app.get(img)

        if not faces:
            print(f"⚠️ No face detected in {filename}")
            continue

        # Take first detected face
        embedding = faces[0].embedding
        embeddings.append(embedding)
        labels.append(LABEL_NAME)

        print(f"✅ Processed {filename}")

# Save embeddings and labels
if embeddings:
    np.save("face_embeddings.npy", np.array(embeddings))  # (N, 512)
    np.save("labels.npy", np.array(labels))
    print(f"\n✅ Saved {len(embeddings)} embeddings.")
else:
    print("❌ No embeddings saved.")
