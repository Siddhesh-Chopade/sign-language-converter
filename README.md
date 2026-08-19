# AI-Driven Sign Language to Text & Speech Conversion with Real-Time Object Recognition

A group project. My role: **frontend development**.

Converts hand signs captured from a webcam into on-screen text and spoken
output in real time, while also recognizing everyday objects in the same
frame for extra context.

## Tech Stack

- **Frontend:** HTML5, CSS3, JavaScript (webcam capture, live UI, Web Speech API)
- **Backend:** Python (Flask, OpenCV, MediaPipe)
- **Database:** MySQL (stores recognized-sign history)

## Project Structure

```
sign-language-converter/
├── frontend/
│   ├── index.html        # Camera view + output panels
│   ├── style.css
│   └── script.js         # Webcam capture, API calls, speech synthesis
├── backend/
│   ├── app.py             # Flask API (predict, history, health)
│   ├── gesture_classifier.py   # Rule-based sign classification
│   ├── object_detector.py      # MobileNet-SSD object detection
│   ├── db.py               # MySQL read/write helpers
│   ├── requirements.txt
│   ├── models/              # Put MobileNetSSD model files here (see below)
│   └── database/
│       └── schema.sql       # Run once to create the database + tables
└── README.md
```

## How It Works

1. The frontend grabs a frame from the webcam roughly every second and
   sends it to the backend as a base64 JPEG.
2. The backend uses **MediaPipe Hands** to find 21 landmark points on the
   hand, then a small rule-based lookup table
   (`gesture_classifier.py`) matches the finger positions against a set
   of known signs (Hello, Yes, No, I Love You, Peace, One, Stop, OK).
3. In the same request, **OpenCV's MobileNet-SSD** model
   (`object_detector.py`) scans the frame for everyday objects
   (person, chair, laptop-adjacent classes, etc.) and returns bounding
   boxes.
4. The frontend displays the recognized sign, speaks it aloud with the
   browser's Web Speech API, draws boxes around detected objects, and
   builds a running sentence out of confirmed signs.
5. Confirmed signs are saved to **MySQL** so there's a session history.

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Download the MobileNet-SSD model files and place them in `backend/models/`:
- `MobileNetSSD_deploy.prototxt`
- `MobileNetSSD_deploy.caffemodel`

(Both are freely available from the original MobileNet-SSD Caffe repo —
search "chuanqi305 MobileNet-SSD".) Object detection is skipped
gracefully if these aren't present yet, so the sign-language part of the
app still works without them.

### 2. Database

```bash
mysql -u root -p < backend/database/schema.sql
```

Then update the password in `backend/db.py` (`DB_CONFIG`) to match your
local MySQL setup.

### 3. Run the backend

```bash
cd backend
python app.py
```

The API runs at `http://127.0.0.1:5000`.

### 4. Run the frontend

Just open `frontend/index.html` in a browser (Chrome recommended for
webcam + speech support). If your browser blocks camera access on a
`file://` page, serve it locally instead:

```bash
cd frontend
python -m http.server 8080
```

Then visit `http://127.0.0.1:8080`.

## Notes

- The gesture set is intentionally small and rule-based (finger-up /
  finger-down patterns) rather than a trained deep learning model —
  it's easy to extend by adding new finger-state combinations to the
  `SIGN_MAP` dictionary in `gesture_classifier.py`.
- CORS is enabled on the Flask app so the frontend can call it from a
  different port/origin during local development.
