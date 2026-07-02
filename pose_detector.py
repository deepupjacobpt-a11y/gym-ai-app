import cv2
import mediapipe as mp
import numpy as np

# ── Setup MediaPipe ──────────────────────────────────────────
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# ── Helper: calculate angle between 3 body points ───────────
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180:
        angle = 360 - angle
    return angle

# ── Main: open camera and detect squats ─────────────────────
cap = cv2.VideoCapture(0)   # 0 = your webcam

counter = 0       # rep counter
stage = None      # "up" or "down"

with mp_pose.Pose(min_detection_confidence=0.5,
                  min_tracking_confidence=0.5) as pose:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert colour for MediaPipe
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Extract landmarks (body points)
        try:
            landmarks = results.pose_landmarks.landmark

            # Get hip, knee, ankle coordinates
            hip = [
                landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y
            ]
            knee = [
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y
            ]
            ankle = [
                landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y
            ]

            # Calculate knee angle
            angle = calculate_angle(hip, knee, ankle)

            # Count reps based on angle
            if angle > 160:
                stage = "up"
            if angle < 90 and stage == "up":
                stage = "down"
                counter += 1

            # Feedback based on angle
            if angle > 160:
                feedback = "Stand tall"
            elif 90 <= angle <= 160:
                feedback = "Going down..."
            else:
                feedback = "Good depth! Come up!"

        except:
            feedback = "Stand in frame"
            angle = 0

        # ── Draw on screen ───────────────────────────────────

        # Black box top-left for rep counter
        cv2.rectangle(image, (0, 0), (230, 80), (0, 0, 0), -1)
        cv2.putText(image, f"REPS: {counter}",
                    (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (0, 255, 0), 2)
        cv2.putText(image, f"Stage: {stage}",
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 1)

        # Feedback bottom of screen
        cv2.rectangle(image, (0, 430), (640, 480), (40, 40, 40), -1)
        cv2.putText(image, feedback,
                    (10, 465),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 255), 2)

        # Draw skeleton on body
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        # Show the camera window
        cv2.imshow("Gym AI - Squat Detector", image)

        # Press Q to quit
        if cv2.waitKey(10) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()