// ---------- Configuration ----------
const API_BASE = "http://127.0.0.1:5000";   // Flask backend URL
const PREDICT_INTERVAL_MS = 900;             // how often we send a frame to the backend
const SIGN_HOLD_TO_CONFIRM = 3;              // consecutive matching predictions before we "confirm" a sign

// ---------- Elements ----------
const webcam = document.getElementById("webcam");
const overlay = document.getElementById("overlay");
const captureCanvas = document.getElementById("captureCanvas");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const speechToggle = document.getElementById("speechToggle");
const liveText = document.getElementById("liveText");
const confidenceFill = document.getElementById("confidenceFill");
const sentenceBox = document.getElementById("sentenceBox");
const clearSentenceBtn = document.getElementById("clearSentence");
const speakSentenceBtn = document.getElementById("speakSentence");
const objectList = document.getElementById("objectList");
const historyList = document.getElementById("historyList");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

const overlayCtx = overlay.getContext("2d");
const captureCtx = captureCanvas.getContext("2d");

let stream = null;
let predictTimer = null;
let lastSpokenSign = "";
let holdCount = 0;
let lastConfirmedSign = "";
let sentenceWords = [];

// ---------- Camera control ----------
async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
    webcam.srcObject = stream;
    await webcam.play();

    overlay.width = webcam.videoWidth || 640;
    overlay.height = webcam.videoHeight || 480;
    captureCanvas.width = overlay.width;
    captureCanvas.height = overlay.height;

    startBtn.disabled = true;
    stopBtn.disabled = false;

    predictTimer = setInterval(captureAndSendFrame, PREDICT_INTERVAL_MS);
    checkServerHealth();
  } catch (err) {
    alert("Could not access the camera: " + err.message);
  }
}

function stopCamera() {
  if (predictTimer) clearInterval(predictTimer);
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }
  overlayCtx.clearRect(0, 0, overlay.width, overlay.height);
  startBtn.disabled = false;
  stopBtn.disabled = true;
}

startBtn.addEventListener("click", startCamera);
stopBtn.addEventListener("click", stopCamera);

// ---------- Frame capture + backend call ----------
function captureAndSendFrame() {
  if (!stream) return;
  captureCtx.drawImage(webcam, 0, 0, captureCanvas.width, captureCanvas.height);
  const frameData = captureCanvas.toDataURL("image/jpeg", 0.7);

  fetch(`${API_BASE}/api/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: frameData })
  })
    .then(res => {
      if (!res.ok) throw new Error("Server error " + res.status);
      return res.json();
    })
    .then(handlePredictionResult)
    .catch(err => {
      setServerStatus(false);
      console.error("Prediction request failed:", err);
    });
}

function handlePredictionResult(data) {
  setServerStatus(true);

  // ----- Sign / gesture result -----
  const sign = data.sign && data.sign.label ? data.sign.label : "No hand detected";
  const confidence = data.sign && data.sign.confidence ? data.sign.confidence : 0;

  liveText.textContent = sign;
  confidenceFill.style.width = Math.round(confidence * 100) + "%";

  // simple "hold to confirm" logic so a fleeting misread doesn't spam speech/sentence
  if (sign === lastConfirmedSign) {
    holdCount++;
  } else {
    lastConfirmedSign = sign;
    holdCount = 1;
  }

  if (holdCount === SIGN_HOLD_TO_CONFIRM && sign !== "No hand detected") {
    onSignConfirmed(sign);
  }

  // ----- Object detection results -----
  renderObjects(data.objects || []);
  drawOverlayBoxes(data.objects || []);
}

function onSignConfirmed(sign) {
  // add to sentence builder
  sentenceWords.push(sign);
  sentenceBox.textContent = sentenceWords.join(" ");

  // speak it (only if changed since last spoken word, to avoid repeats)
  if (speechToggle.checked && sign !== lastSpokenSign) {
    speak(sign);
    lastSpokenSign = sign;
  }

  // add to on-screen history + persist to backend (which writes to MySQL)
  addHistoryEntry(sign);
  fetch(`${API_BASE}/api/history`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sign_text: sign })
  }).catch(err => console.error("Could not save history:", err));
}

// ---------- Speech ----------
function speak(text) {
  if (!("speechSynthesis" in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  window.speechSynthesis.speak(utterance);
}

speakSentenceBtn.addEventListener("click", () => {
  if (sentenceWords.length) speak(sentenceWords.join(" "));
});

clearSentenceBtn.addEventListener("click", () => {
  sentenceWords = [];
  sentenceBox.textContent = "";
});

// ---------- Object list + bounding boxes ----------
function renderObjects(objects) {
  if (!objects.length) {
    objectList.innerHTML = `<li class="empty">No objects detected yet</li>`;
    return;
  }
  objectList.innerHTML = objects
    .map(obj => `<li><span>${obj.label}</span><span class="conf">${Math.round(obj.confidence * 100)}%</span></li>`)
    .join("");
}

function drawOverlayBoxes(objects) {
  overlayCtx.clearRect(0, 0, overlay.width, overlay.height);
  overlayCtx.lineWidth = 2;
  overlayCtx.font = "14px Segoe UI, sans-serif";

  objects.forEach(obj => {
    const [x, y, w, h] = obj.box; // expected as pixel coords from backend
    overlayCtx.strokeStyle = "#22d3ee";
    overlayCtx.strokeRect(x, y, w, h);
    overlayCtx.fillStyle = "#22d3ee";
    overlayCtx.fillRect(x, y - 18, overlayCtx.measureText(obj.label).width + 10, 18);
    overlayCtx.fillStyle = "#0f1420";
    overlayCtx.fillText(obj.label, x + 5, y - 5);
  });
}

// ---------- History list (client side, mirrors what's saved in MySQL) ----------
function addHistoryEntry(sign) {
  const emptyEl = historyList.querySelector(".empty");
  if (emptyEl) emptyEl.remove();

  const li = document.createElement("li");
  const time = new Date().toLocaleTimeString();
  li.innerHTML = `<span>${sign}</span><span class="time">${time}</span>`;
  historyList.prepend(li);

  // keep the list from growing forever
  while (historyList.children.length > 15) {
    historyList.removeChild(historyList.lastChild);
  }
}

function loadHistoryFromServer() {
  fetch(`${API_BASE}/api/history`)
    .then(res => res.json())
    .then(rows => {
      if (!rows.length) return;
      historyList.innerHTML = "";
      rows.forEach(row => addHistoryEntry(row.sign_text));
    })
    .catch(err => console.error("Could not load history:", err));
}

// ---------- Server status ----------
function setServerStatus(isOnline) {
  statusDot.classList.toggle("online", isOnline);
  statusText.textContent = isOnline ? "Connected to server" : "Server unreachable";
}

function checkServerHealth() {
  fetch(`${API_BASE}/api/health`)
    .then(res => res.json())
    .then(() => {
      setServerStatus(true);
      loadHistoryFromServer();
    })
    .catch(() => setServerStatus(false));
}

// initial check on page load (before the camera even starts)
checkServerHealth();
