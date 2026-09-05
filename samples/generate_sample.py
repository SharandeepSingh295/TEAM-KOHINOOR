"""
Generates and downloads test sample face images for VeriFace-Chain.
"""

import os
import cv2
import numpy as np
import requests

def create_synthetic_face(output_path: str = "samples/sample_face.jpg"):
    """
    Creates a synthetic stylized face image with landmarks (eyes, nose, mouth)
    and gradient skin tones suitable for testing face detection pipelines.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 400x400 RGB image
    img = np.full((400, 400, 3), (240, 240, 240), dtype=np.uint8)
    
    # Head contour (oval)
    cv2.ellipse(img, (200, 200), (110, 140), 0, 0, 360, (190, 210, 245), -1)
    cv2.ellipse(img, (200, 200), (110, 140), 0, 0, 360, (130, 150, 190), 2)
    
    # Eyes
    cv2.circle(img, (160, 170), 16, (255, 255, 255), -1)
    cv2.circle(img, (240, 170), 16, (255, 255, 255), -1)
    cv2.circle(img, (160, 170), 8, (60, 40, 30), -1)
    cv2.circle(img, (240, 170), 8, (60, 40, 30), -1)
    
    # Eyebrows
    cv2.line(img, (140, 150), (180, 150), (40, 30, 20), 3)
    cv2.line(img, (220, 150), (260, 150), (40, 30, 20), 3)
    
    # Nose
    pts = np.array([[200, 185], [192, 220], [208, 220]], np.int32)
    cv2.polylines(img, [pts], True, (130, 150, 190), 2)
    
    # Mouth (smile)
    cv2.ellipse(img, (200, 250), (40, 20), 0, 0, 180, (80, 80, 180), 3)
    
    cv2.imwrite(output_path, img)
    print(f"Synthetic face generated at: {output_path}")
    return output_path

def download_real_sample(output_path: str = "samples/real_sample_face.jpg"):
    """
    Downloads a high-quality public domain face portrait for real-world face detection tests.
    """
    url = "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=500&auto=format&fit=crop&q=80"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(resp.content)
            print(f"Real portrait sample downloaded to: {output_path}")
            return output_path
    except Exception as e:
        print(f"Note: could not download online sample: {e}")
    return None

if __name__ == "__main__":
    create_synthetic_face()
    download_real_sample()
