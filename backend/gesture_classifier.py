"""
gesture_classifier.py
----------------------
A simple, rule-based sign-language classifier.

Instead of training a deep learning model, this uses MediaPipe's hand
landmark detector to find 21 key points on the hand, works out which
fingers are extended, and matches that pattern against a small lookup
table of signs. This keeps the project understandable while still
giving real-time recognition.

Landmark indices (from MediaPipe Hands):
  0  = wrist
  4  = thumb tip        3 = thumb IP joint
  8  = index tip         6 = index PIP joint
  12 = middle tip       10 = middle PIP joint
  16 = ring tip         14 = ring PIP joint
  20 = pinky tip        18 = pinky PIP joint
"""

FINGER_TIPS = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}
FINGER_PIPS = {"thumb": 3, "index": 6, "middle": 10, "ring": 14, "pinky": 18}

# Sign lookup table: (thumb, index, middle, ring, pinky) -> label
# True = finger extended, False = finger folded
SIGN_MAP = {
    (False, False, False, False, False): "No",
    (True, True, True, True, True): "Hello",
    (True, False, False, False, False): "Yes",
    (True, True, False, False, True): "I Love You",
    (False, True, True, False, False): "Peace",
    (False, True, False, False, False): "One",
    (False, True, True, True, True): "Stop",
    (True, True, True, False, False): "OK",
}


def _fingers_extended(landmarks):
    """
    landmarks: list of 21 (x, y) points, already normalized to the image.
    Returns a tuple of 5 booleans, one per finger, True if extended.
    """
    states = []

    # Thumb: compare x position against the joint below it (works reasonably
    # well for a hand facing the camera; mirrored hands will need calibration).
    thumb_tip = landmarks[FINGER_TIPS["thumb"]]
    thumb_pip = landmarks[FINGER_PIPS["thumb"]]
    states.append(abs(thumb_tip[0] - thumb_pip[0]) > 0.04)

    # Other four fingers: extended if the tip is higher (smaller y) than the
    # PIP joint beneath it.
    for finger in ["index", "middle", "ring", "pinky"]:
        tip = landmarks[FINGER_TIPS[finger]]
        pip = landmarks[FINGER_PIPS[finger]]
        states.append(tip[1] < pip[1])

    return tuple(states)


def classify_hand(landmarks):
    """
    Takes 21 (x, y) landmark points and returns a dict:
      { "label": str, "confidence": float }
    """
    if not landmarks or len(landmarks) < 21:
        return {"label": "No hand detected", "confidence": 0.0}

    finger_state = _fingers_extended(landmarks)
    label = SIGN_MAP.get(finger_state)

    if label is None:
        return {"label": "Unrecognized gesture", "confidence": 0.35}

    # Rule-based match, so we report a fixed high confidence for a clean match.
    return {"label": label, "confidence": 0.92}
