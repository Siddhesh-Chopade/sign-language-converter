"""
app.py
------
Flask backend for the AI-Driven Sign Language to Text & Speech
Conversion project.

Responsibilities:
  1. Receive a webcam frame from the frontend (base64 JPEG).
  2. Run MediaPipe Hands to find hand landmarks, then classify the
     gesture using the rule-based logic in gesture_classifier.py.
  3. Run object detection on the same frame using object_detector.py.
  4. Return both results as JSON.
  5. Save confirmed signs to MySQL and serve back recent history.
"""

import base64
import numpy as np
import cv2
import mediapipe as mp
from flask import Flask, request, jsonify
from flask_cors import CORS

from gesture_classifier import classify_hand
from object_detector import detect_objects
import db

app = Flask(__name__)
CORS(app)  # allow the frontend (served from a different origin) to call this API

mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5,
)


def decode_base64_image(data_url):
    """Convert a 'data:image/jpeg;base64,...' string into an OpenCV BGR image."""
    header, encoded = data_url.split(",", 1)
    binary_data = base64.b64decode(encoded)
    np_array = np.frombuffer(binary_data, dtype=np.uint8)
    frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    return frame


def extract_landmarks(frame_bgr):
    """Run MediaPipe Hands and return a list of (x, y) points, or None."""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    results = hands_detector.process(frame_rgb)

    if not results.multi_hand_landmarks:
        return None

    hand = results.multi_hand_landmarks[0]
    return [(point.x, point.y) for point in hand.landmark]


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/predict", methods=["POST"])
def predict():
    payload = request.get_json(silent=True) or {}
    image_data = payload.get("image")

    if not image_data:
        return jsonify({"error": "No image provided"}), 400

    frame = decode_base64_image(image_data)
    if frame is None:
        return jsonify({"error": "Could not decode image"}), 400

    # 1. Sign language recognition
    landmarks = extract_landmarks(frame)
    sign_result = classify_hand(landmarks)

    # 2. Real-time object recognition (runs on the same frame)
    object_results = detect_objects(frame)

    return jsonify({
        "sign": sign_result,
        "objects": object_results,
    })


@app.route("/api/history", methods=["GET"])
def get_history():
    rows = db.get_recent_signs(limit=15)
    # Convert datetime objects to strings so they're JSON-serializable
    for row in rows:
        if "created_at" in row and row["created_at"] is not None:
            row["created_at"] = str(row["created_at"])
    return jsonify(rows)


@app.route("/api/history", methods=["POST"])
def save_history():
    payload = request.get_json(silent=True) or {}
    sign_text = payload.get("sign_text")
    confidence = payload.get("confidence", 0.9)

    if not sign_text:
        return jsonify({"error": "sign_text is required"}), 400

    db.insert_sign(sign_text, confidence)
    return jsonify({"status": "saved"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
