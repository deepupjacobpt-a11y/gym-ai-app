from flask import Flask, request, jsonify
import mediapipe as mp
import numpy as np
import cv2
import base64

# ── Create Flask app ─────────────────────────────────────────
app = Flask(__name__)

# ── Setup MediaPipe ──────────────────────────────────────────
mp_pose = mp.solutions.pose

# ── Track rep stages per session ────────────────────────────
rep_state = {}

# ── Helper: calculate angle between 3 points ────────────────
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - \
              np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180 else angle

# ── Home route ───────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Gym AI API is running!"})

# ── Analyse route ────────────────────────────────────────────
@app.route("/analyse", methods=["POST"])
def analyse():
    try:
        data = request.json

        # Check if request is empty or missing image
        if not data or "image" not in data:
            return jsonify({
                "detected": False,
                "feedback": "No image received"
            }), 400

        image_data = base64.b64decode(data["image"])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({
                "detected": False,
                "feedback": "Invalid image data"
            }), 400

        with mp_pose.Pose() as pose:
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)

            if not results.pose_landmarks:
                return jsonify({
                    "detected": False,
                    "feedback": "No person detected — stand in frame"
                })

            lm = results.pose_landmarks.landmark

            hip = [
                lm[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                lm[mp_pose.PoseLandmark.LEFT_HIP.value].y
            ]
            knee = [
                lm[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                lm[mp_pose.PoseLandmark.LEFT_KNEE.value].y
            ]
            ankle = [
                lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].y
            ]

            angle = calculate_angle(hip, knee, ankle)

            prev_stage = rep_state.get("default", "up")
            rep_counted = False

            if angle > 160:
                current_stage = "up"
                feedback = "Ready — go lower to start rep"
            elif angle < 90:
                current_stage = "down"
                feedback = "Great depth! Now come back up"
            else:
                current_stage = prev_stage
                feedback = "Keep going lower..."

            if prev_stage == "down" and current_stage == "up":
                rep_counted = True

            rep_state["default"] = current_stage

            return jsonify({
                "detected":    True,
                "angle":       round(angle, 1),
                "stage":       current_stage,
                "feedback":    feedback,
                "rep_counted": rep_counted
            })

    except Exception as e:
        return jsonify({
            "detected": False,
            "feedback": f"Server error: {str(e)}"
        }), 500

# ── Run the app ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)