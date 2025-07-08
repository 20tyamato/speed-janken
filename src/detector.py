# src/detector.py
import math
import warnings

import mediapipe as mp
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")


class HandGestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.7,
        )
        self.mp_drawing = mp.solutions.drawing_utils

        self.gesture_buffer = []
        self.buffer_size = 5
        self.confidence_threshold = 0.6

    def calculate_distance(self, point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def calculate_angle(self, point1, point2, point3):
        vector1 = (point1[0] - point2[0], point1[1] - point2[1])
        vector2 = (point3[0] - point2[0], point3[1] - point2[1])

        dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]
        magnitude1 = math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
        magnitude2 = math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)

        if magnitude1 == 0 or magnitude2 == 0:
            return 0

        cos_angle = dot_product / (magnitude1 * magnitude2)
        cos_angle = max(-1, min(1, cos_angle))

        return math.acos(cos_angle) * 180 / math.pi

    def is_finger_extended(self, landmarks, finger_tip, finger_pip, finger_mcp=None):
        if finger_mcp is not None:
            tip_to_mcp = self.calculate_distance(
                landmarks[finger_tip], landmarks[finger_mcp]
            )
            pip_to_mcp = self.calculate_distance(
                landmarks[finger_pip], landmarks[finger_mcp]
            )
            return tip_to_mcp > pip_to_mcp * 1.2
        else:
            return landmarks[finger_tip][1] < landmarks[finger_pip][1]

    def is_thumb_extended(self, landmarks):
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_cmc = landmarks[1]

        tip_to_cmc_dist = self.calculate_distance(thumb_tip, thumb_cmc)
        ip_to_cmc_dist = self.calculate_distance(thumb_ip, thumb_cmc)

        is_extended = tip_to_cmc_dist > ip_to_cmc_dist * 1.3

        palm_center = landmarks[9]
        thumb_distance = self.calculate_distance(thumb_tip, palm_center)

        return is_extended and thumb_distance > 0.08

    def detect_scissors_improved(self, landmarks):
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        index_mcp = landmarks[5]

        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        middle_mcp = landmarks[9]

        ring_tip = landmarks[16]
        ring_pip = landmarks[14]

        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]

        thumb_tip = landmarks[4]
        thumb_pip = landmarks[3]

        index_extended = (
            index_tip[1] < index_pip[1] - 0.03
            and self.calculate_distance(index_tip, index_mcp)
            > self.calculate_distance(index_pip, index_mcp) * 1.3
        )

        middle_extended = (
            middle_tip[1] < middle_pip[1] - 0.03
            and self.calculate_distance(middle_tip, middle_mcp)
            > self.calculate_distance(middle_pip, middle_mcp) * 1.3
        )

        ring_folded = ring_tip[1] > ring_pip[1] + 0.01
        pinky_folded = pinky_tip[1] > pinky_pip[1] + 0.01
        both_fingers_folded = ring_folded and pinky_folded

        thumb_folded = (
            thumb_tip[1] > thumb_pip[1]
            or self.calculate_distance(thumb_tip, landmarks[9]) < 0.1
        )

        fingers_distance = self.calculate_distance(index_tip, middle_tip)
        fingers_separation = fingers_distance > 0.05 and fingers_distance < 0.15

        index_much_higher = (
            index_tip[1] < ring_tip[1] - 0.03 and index_tip[1] < pinky_tip[1] - 0.03
        )
        middle_much_higher = (
            middle_tip[1] < ring_tip[1] - 0.03 and middle_tip[1] < pinky_tip[1] - 0.03
        )

        not_all_folded = not (
            ring_folded
            and pinky_folded
            and index_tip[1] > index_pip[1]
            and middle_tip[1] > middle_pip[1]
        )

        scissors_conditions = [
            index_extended,
            middle_extended,
            both_fingers_folded,
            thumb_folded,
            fingers_separation,
            index_much_higher,
            middle_much_higher,
            not_all_folded,
        ]

        scissors_score = sum(scissors_conditions)

        return scissors_score >= 7

    def detect_gesture_detailed(self, landmarks):
        fingers_extended = []

        thumb_extended = self.is_thumb_extended(landmarks)
        fingers_extended.append(thumb_extended)

        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        finger_mcps = [5, 9, 13, 17]

        for i in range(4):
            extended = self.is_finger_extended(
                landmarks, finger_tips[i], finger_pips[i], finger_mcps[i]
            )
            fingers_extended.append(extended)

        extended_count = sum(fingers_extended)
        if extended_count == 0:
            return "rock"
        if self.detect_scissors_improved(landmarks):
            return "scissors"
        elif extended_count == 5:
            finger_tips_landmarks = [
                landmarks[4],
                landmarks[8],
                landmarks[12],
                landmarks[16],
                landmarks[20],
            ]

            min_distance = float("inf")
            for i in range(len(finger_tips_landmarks)):
                for j in range(i + 1, len(finger_tips_landmarks)):
                    dist = self.calculate_distance(
                        finger_tips_landmarks[i], finger_tips_landmarks[j]
                    )
                    min_distance = min(min_distance, dist)

            if min_distance > 0.04:
                return "paper"
        return "unknown"

    def detect_gesture(self, landmarks):
        current_gesture = self.detect_gesture_detailed(landmarks)

        self.gesture_buffer.append(current_gesture)
        if len(self.gesture_buffer) > self.buffer_size:
            self.gesture_buffer.pop(0)

        if len(self.gesture_buffer) < self.buffer_size:
            return "unknown"

        gesture_counts = {}
        for gesture in self.gesture_buffer:
            gesture_counts[gesture] = gesture_counts.get(gesture, 0) + 1

        if gesture_counts:
            most_common_gesture = max(gesture_counts, key=gesture_counts.get)
            confidence = gesture_counts[most_common_gesture] / len(self.gesture_buffer)
            if (
                confidence >= self.confidence_threshold
                and most_common_gesture != "unknown"
            ):
                return most_common_gesture

        return "unknown"
