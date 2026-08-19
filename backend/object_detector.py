"""
object_detector.py
-------------------
Runs real-time object detection using OpenCV's DNN module with a
pre-trained MobileNet-SSD model (Caffe format). This gives basic object
recognition (person, chair, laptop, phone, etc.) without needing to
train anything ourselves.

Model files are NOT bundled with this project (they're a few MB and
have their own license). Download them once and place them in
backend/models/:

  1. MobileNetSSD_deploy.prototxt
  2. MobileNetSSD_deploy.caffemodel

Both are widely available from the original MobileNet-SSD Caffe repo,
e.g. https://github.com/chuanqi305/MobileNet-SSD
"""

import os
import cv2
import numpy as np

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
PROTOTXT_PATH = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.prototxt")
WEIGHTS_PATH = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.caffemodel")

CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus",
    "car", "cat", "chair", "cow", "diningtable", "dog", "horse",
    "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"
]

CONFIDENCE_THRESHOLD = 0.5

_net = None


def _load_network():
    global _net
    if _net is not None:
        return _net

    if not (os.path.exists(PROTOTXT_PATH) and os.path.exists(WEIGHTS_PATH)):
        print(
            "[object_detector] Model files not found in backend/models/. "
            "Object detection will be skipped until they're added. "
            "See the comment at the top of object_detector.py for download info."
        )
        return None

    _net = cv2.dnn.readNetFromCaffe(PROTOTXT_PATH, WEIGHTS_PATH)
    return _net


def detect_objects(frame_bgr):
    """
    frame_bgr: an OpenCV image (numpy array, BGR).
    Returns a list of dicts: { "label": str, "confidence": float, "box": [x, y, w, h] }
    """
    net = _load_network()
    if net is None:
        return []

    height, width = frame_bgr.shape[:2]
    blob = cv2.dnn.blobFromImage(frame_bgr, 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    results = []
    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < CONFIDENCE_THRESHOLD:
            continue

        class_id = int(detections[0, 0, i, 1])
        if class_id < 0 or class_id >= len(CLASSES):
            continue
        label = CLASSES[class_id]
        if label == "background":
            continue

        box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
        (x1, y1, x2, y2) = box.astype("int")
        results.append({
            "label": label,
            "confidence": round(confidence, 2),
            "box": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
        })

    return results
