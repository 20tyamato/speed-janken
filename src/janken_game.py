# src/janken_game.py
import math
import random
import time
import warnings

import cv2
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
from pygame.locals import *

from src.common import logger
from src.detector import HandGestureDetector
from src.particle import ParticleSystem

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")


class JankenGame:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        pygame.init()
        self.screen = pygame.display.set_mode((1400, 1000), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Reflex Rock Paper Scissors")

        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, 1400 / 1000, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)

        pygame.font.init()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)

        self.particle_system = ParticleSystem()
        self.hand_detector = HandGestureDetector()

        self.camera_texture = None

        self.game_states = ["MENU", "COUNTDOWN", "SHOW_HANDS", "DETECT", "RESULT"]
        self.current_state = "MENU"
        self.round_count = 0
        self.player_wins = 0
        self.computer_wins = 0
        self.draws = 0

        self.state_start_time = time.time()
        self.countdown_numbers = [3, 2, 1]
        self.countdown_index = 0

        self.countdown_duration = 0.5
        self.show_duration = 0.3
        self.detect_duration = 1.0
        self.result_duration = 1.5

        self.gestures = ["rock", "paper", "scissors"]
        self.gesture_names = {"rock": "Rock", "paper": "Paper", "scissors": "Scissors"}
        self.gesture_emojis = {"rock": "✊", "paper": "✋", "scissors": "✌️"}

        self.computer_gesture = None
        self.player_gesture = None
        self.game_result = None

        self.reaction_start_time = None
        self.reaction_time = None

    def judge_winner(self, player, computer):
        if player == computer:
            return "draw"
        elif (
            (player == "rock" and computer == "scissors")
            or (player == "scissors" and computer == "paper")
            or (player == "paper" and computer == "rock")
        ):
            return "win"
        else:
            return "lose"

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hand_detector.hands.process(rgb_frame)

        previous_gesture = self.player_gesture
        self.player_gesture = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.hand_detector.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.hand_detector.mp_hands.HAND_CONNECTIONS
                )
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.append([lm.x, lm.y])

                gesture = self.hand_detector.detect_gesture(landmarks)
                if gesture != "unknown":
                    self.player_gesture = gesture

                    if (
                        self.current_state == "DETECT"
                        and previous_gesture is None
                        and self.reaction_start_time is not None
                    ):
                        self.reaction_time = time.time() - self.reaction_start_time
        else:
            self.hand_detector.gesture_buffer = []

        return frame

    # notes: カメラの映像をOpenGLのテクスチャとして作成するメソッド
    def create_camera_texture(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.flip(frame_rgb, 0)

        height, width, channels = frame_rgb.shape

        if self.camera_texture is not None:
            glDeleteTextures([self.camera_texture])

        self.camera_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.camera_texture)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            width,
            height,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            frame_rgb,
        )

        return self.camera_texture

    # notes: カメラの映像を描画するメソッド
    def draw_textured_quad(self, texture_id, x, y, z, width, height):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor3f(1, 1, 1)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex3f(x - width / 2, y - height / 2, z)
        glTexCoord2f(1, 0)
        glVertex3f(x + width / 2, y - height / 2, z)
        glTexCoord2f(1, 1)
        glVertex3f(x + width / 2, y + height / 2, z)
        glTexCoord2f(0, 1)
        glVertex3f(x - width / 2, y + height / 2, z)
        glEnd()

        glDisable(GL_TEXTURE_2D)

    def draw_3d_hand_model(self, gesture, x, y, z, scale=1.0, color=(1, 1, 1)):
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(scale, scale, scale)
        glColor3f(*color)

        if gesture == "rock":
            glBegin(GL_QUADS)
            for i in range(8):
                angle = i * 45 * math.pi / 180
                x1 = math.cos(angle) * 1.5
                z1 = math.sin(angle) * 1.5
                x2 = math.cos(angle + 45 * math.pi / 180) * 1.5
                z2 = math.sin(angle + 45 * math.pi / 180) * 1.5

                glVertex3f(x1, -1, z1)
                glVertex3f(x1, 1, z1)
                glVertex3f(x2, 1, z2)
                glVertex3f(x2, -1, z2)
            glEnd()

        elif gesture == "paper":
            glBegin(GL_QUADS)
            glVertex3f(-1.5, -2, 0)
            glVertex3f(1.5, -2, 0)
            glVertex3f(1.5, 1, 0)
            glVertex3f(-1.5, 1, 0)

            fingers_x = [-1, -0.5, 0, 0.5, 1]
            for fx in fingers_x:
                glVertex3f(fx - 0.2, 1, 0)
                glVertex3f(fx + 0.2, 1, 0)
                glVertex3f(fx + 0.2, 3, 0)
                glVertex3f(fx - 0.2, 3, 0)
            glEnd()

        elif gesture == "scissors":
            glBegin(GL_QUADS)
            glVertex3f(-1, -2, 0)
            glVertex3f(1, -2, 0)
            glVertex3f(1, 0, 0)
            glVertex3f(-1, 0, 0)

            glVertex3f(-0.7, 0, 0)
            glVertex3f(-0.3, 0, 0)
            glVertex3f(0, 3, 0)
            glVertex3f(-0.4, 3, 0)

            glVertex3f(0.3, 0, 0)
            glVertex3f(0.7, 0, 0)
            glVertex3f(0.4, 3, 0)
            glVertex3f(0, 3, 0)
            glEnd()

        glPopMatrix()

    def update_game_state(self):
        current_time = time.time()
        elapsed = current_time - self.state_start_time

        if self.current_state == "MENU":
            pass

        elif self.current_state == "COUNTDOWN":
            if elapsed >= self.countdown_duration:
                self.countdown_index += 1
                self.state_start_time = current_time
                self.particle_system.add_effect("countdown", 15)

                if self.countdown_index >= len(self.countdown_numbers):
                    self.show_hands()

        elif self.current_state == "SHOW_HANDS":
            if elapsed >= self.show_duration:
                self.start_detection()

        elif self.current_state == "DETECT":
            if elapsed >= self.detect_duration:
                if self.player_gesture:
                    self.game_result = self.judge_winner(
                        self.player_gesture, self.computer_gesture
                    )
                else:
                    self.game_result = "lose"

                self.show_result()

        elif self.current_state == "RESULT":
            if elapsed >= self.result_duration:
                self.next_round()

    def start_countdown(self):
        self.current_state = "COUNTDOWN"
        self.state_start_time = time.time()
        self.countdown_index = 0
        self.computer_gesture = random.choice(self.gestures)
        self.player_gesture = None
        self.game_result = None
        self.reaction_time = None
        self.particle_system.clear_particles()

        self.hand_detector.gesture_buffer = []

        logger.info(f"Round {self.round_count + 1} - Reflex Battle!")

    def show_hands(self):
        self.current_state = "SHOW_HANDS"
        self.state_start_time = time.time()
        logger.info(f"Computer plays: {self.gesture_names[self.computer_gesture]}")

    def start_detection(self):
        self.current_state = "DETECT"
        self.state_start_time = time.time()
        self.reaction_start_time = time.time()
        logger.info("Quickly show your hand!")

    def show_result(self):
        self.current_state = "RESULT"
        self.state_start_time = time.time()

        if self.game_result == "win":
            self.player_wins += 1
            self.particle_system.add_effect("win", 80)
            reaction_msg = (
                f" (Reaction time: {self.reaction_time:.3f}s)"
                if self.reaction_time
                else ""
            )
            logger.info(
                f"YOU WIN! {self.gesture_names[self.player_gesture]} beats {self.gesture_names[self.computer_gesture]}{reaction_msg}"
            )
        elif self.game_result == "lose":
            self.computer_wins += 1
            self.particle_system.add_effect("lose", 60)
            if self.player_gesture:
                reaction_msg = (
                    f" (Reaction time: {self.reaction_time:.3f}s)"
                    if self.reaction_time
                    else ""
                )
                logger.info(
                    f"YOU LOSE! {self.gesture_names[self.computer_gesture]} beats {self.gesture_names[self.player_gesture]}{reaction_msg}"
                )
            else:
                logger.info("YOU LOSE! Too slow!")
        else:
            self.draws += 1
            self.particle_system.add_effect("draw", 40)
            reaction_msg = (
                f" (Reaction time: {self.reaction_time:.3f}s)"
                if self.reaction_time
                else ""
            )
            logger.info(
                f"DRAW! Both played {self.gesture_names[self.computer_gesture]}{reaction_msg}"
            )

    def next_round(self):
        self.round_count += 1
        self.current_state = "MENU"
        self.state_start_time = time.time()
        logger.info(
            f"Score: You {self.player_wins} - {self.computer_wins} Computer (Draws: {self.draws})"
        )
        logger.info("SPACE for next round, ESC to quit")

    def reset_game(self):
        self.current_state = "MENU"
        self.round_count = 0
        self.player_wins = 0
        self.computer_wins = 0
        self.draws = 0
        self.state_start_time = time.time()
        self.particle_system.clear_particles()

    def draw_scene(self):
        if self.current_state == "COUNTDOWN":
            glClearColor(0.1, 0.1, 0.3, 1.0)
        elif self.current_state in ["SHOW_HANDS", "DETECT"]:
            glClearColor(0.2, 0.1, 0.1, 1.0)
        elif self.current_state == "RESULT":
            if self.game_result == "win":
                glClearColor(0.1, 0.3, 0.1, 1.0)
            elif self.game_result == "lose":
                glClearColor(0.3, 0.1, 0.1, 1.0)
            else:
                glClearColor(0.1, 0.2, 0.3, 1.0)
        else:
            glClearColor(0.05, 0.05, 0.15, 1.0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glTranslatef(0.0, 0.0, -20.0)

        self.particle_system.update()
        self.particle_system.draw()

        self.draw_game_ui()

        if hasattr(self, "current_frame") and self.camera_texture:
            self.draw_camera_feed()

        if (
            self.current_state in ["SHOW_HANDS", "DETECT", "RESULT"]
            and self.computer_gesture
        ):
            self.draw_computer_hand()
        if self.player_gesture:
            self.draw_player_hand()

    # notes: ゲームのUIを描画するメソッド
    # ゲームのスコア、ラウンド数、リアクションタイムなどを表示
    def draw_game_ui(self):
        glDisable(GL_DEPTH_TEST)

        score_text = f"YOU: {self.player_wins}  COMPUTER: {self.computer_wins}  DRAW: {self.draws}"
        glColor3f(1, 1, 1)
        glRasterPos3f(-8, 10, -15)
        for char in score_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

        round_text = f"ROUND: {self.round_count + 1}"
        glRasterPos3f(-8, 9, -15)
        for char in round_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

        if self.reaction_time:
            reaction_text = f"REACTION TIME: {self.reaction_time:.3f}s"
            glColor3f(1, 1, 0)
            glRasterPos3f(1, 10, -15)
            for char in reaction_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

        if len(self.hand_detector.gesture_buffer) > 0:
            buffer_info = (
                f"Detection Buffer: {'/'.join(self.hand_detector.gesture_buffer[-3:])}"
            )
            confidence = (
                self.hand_detector.gesture_buffer.count(self.player_gesture)
                / len(self.hand_detector.gesture_buffer)
                if self.player_gesture
                else 0
            )
            glColor3f(0.7, 0.7, 0.7)
            glRasterPos3f(1, 9, -15)
            for char in buffer_info:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

            if confidence > 0:
                conf_text = f"Confidence: {confidence:.1%}"
                glRasterPos3f(1, 8.5, -15)
                for char in conf_text:
                    glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

        if self.current_state == "MENU":
            glColor3f(0, 1, 1)
            msg = "Press SPACE to start the reflex game!"
            glRasterPos3f(-5, 0, -15)
            for char in msg:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

            glColor3f(0.8, 0.8, 0.8)
            tips = [
                "Detection Tips:",
                "✊ Rock: Firmly close all fingers",
                "✋ Paper: Spread fingers wide",
                "✌️ Scissors: Make a V with index and middle fingers",
            ]
            for i, tip in enumerate(tips):
                glRasterPos3f(-7, -2 - i * 0.5, -15)
                for char in tip:
                    glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

        elif self.current_state == "COUNTDOWN" and self.countdown_index < len(
            self.countdown_numbers
        ):
            glColor3f(1, 1, 0)
            number = str(self.countdown_numbers[self.countdown_index])
            glPushMatrix()
            glTranslatef(0, 2, -15)
            glScalef(4, 4, 4)
            glBegin(GL_LINES)
            if number == "3":
                glVertex3f(-0.5, 1, 0)
                glVertex3f(0.5, 1, 0)
                glVertex3f(0.5, 1, 0)
                glVertex3f(0.5, 0, 0)
                glVertex3f(-0.5, 0, 0)
                glVertex3f(0.5, 0, 0)
                glVertex3f(0.5, 0, 0)
                glVertex3f(0.5, -1, 0)
                glVertex3f(-0.5, -1, 0)
                glVertex3f(0.5, -1, 0)
            elif number == "2":
                glVertex3f(-0.5, 1, 0)
                glVertex3f(0.5, 1, 0)
                glVertex3f(0.5, 1, 0)
                glVertex3f(0.5, 0, 0)
                glVertex3f(-0.5, 0, 0)
                glVertex3f(0.5, 0, 0)
                glVertex3f(-0.5, 0, 0)
                glVertex3f(-0.5, -1, 0)
                glVertex3f(-0.5, -1, 0)
                glVertex3f(0.5, -1, 0)
            elif number == "1":
                glVertex3f(0, 1, 0)
                glVertex3f(0, -1, 0)
                glVertex3f(-0.2, 0.8, 0)
                glVertex3f(0, 1, 0)
            glEnd()
            glPopMatrix()

        elif self.current_state == "SHOW_HANDS":
            glColor3f(1, 0.5, 0)
            msg = f"COMPUTER: {self.gesture_names[self.computer_gesture]} - Get Ready!"
            glRasterPos3f(-4, -6, -15)
            for char in msg:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

        elif self.current_state == "DETECT":
            glColor3f(1, 0, 0)
            elapsed = time.time() - self.state_start_time
            remaining = self.detect_duration - elapsed
            msg = f"Show your hand quickly! ({remaining:.1f}s)"
            glRasterPos3f(-4, -6, -15)
            for char in msg:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

            if self.player_gesture:
                glColor3f(0, 1, 0)
                detected_msg = f"Detecting: {self.gesture_names[self.player_gesture]}"
                glRasterPos3f(-3, -7, -15)
                for char in detected_msg:
                    glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

        elif self.current_state == "RESULT":
            if self.game_result == "win":
                glColor3f(0, 1, 0)
                msg = "YOU WIN! 🎉"
            elif self.game_result == "lose":
                glColor3f(1, 0, 0)
                msg = "YOU LOSE... 😞"
            else:
                glColor3f(0, 1, 1)
                msg = "DRAW! 🤝"

            glRasterPos3f(-2, 0, -15)
            for char in msg:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

        glEnable(GL_DEPTH_TEST)

    # notes: カメラの映像を描画するメソッド
    def draw_camera_feed(self):
        if self.camera_texture:
            self.draw_textured_quad(self.camera_texture, -6, 4, -15, 6, 4.5)

            glColor3f(1, 1, 1)
            glBegin(GL_LINE_LOOP)
            glVertex3f(-9, 1.75, -15)
            glVertex3f(-3, 1.75, -15)
            glVertex3f(-3, 6.25, -15)
            glVertex3f(-9, 6.25, -15)
            glEnd()

    # notes: コンピューターの手を描画するメソッド
    def draw_computer_hand(self):
        pulse = (math.sin(time.time() * 8) + 1) * 0.2 + 0.8
        color = (
            (1.0, 0.7, 0.2) if self.current_state == "SHOW_HANDS" else (0.8, 0.8, 0.8)
        )

        self.draw_3d_hand_model(
            self.computer_gesture, 4, 0, -15, scale=2.5 * pulse, color=color
        )

        glColor3f(1, 0.7, 0.2)
        glRasterPos3f(2, -4, -15)
        label = f"COMPUTER: {self.gesture_names[self.computer_gesture]} {self.gesture_emojis[self.computer_gesture]}"
        for char in label:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

    # notes: プレイヤーの手を描画するメソッド
    def draw_player_hand(self):
        color = (0.2, 1.0, 0.2) if self.player_gesture else (0.5, 0.5, 0.5)

        if self.player_gesture:
            self.draw_3d_hand_model(
                self.player_gesture, -4, -2, -15, scale=2.0, color=color
            )

            glColor3f(0.2, 1.0, 0.2)
            glRasterPos3f(-7, -5, -15)
            label = f"YOU: {self.gesture_names[self.player_gesture]} {self.gesture_emojis[self.player_gesture]}"
            for char in label:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

    def run(self):
        glutInit()

        clock = pygame.time.Clock()
        running = True
        logger.info("=== Reflex Rock Paper Scissors ===")
        logger.info("SPACE - Start Game")
        logger.info("R - Reset")
        logger.info("ESC - Quit")
        logger.info("\nRules:")
        logger.info("After a quick countdown, computer's hand will be shown briefly")
        logger.info("Show your hand to the camera immediately!")
        logger.info("Reaction time will be measured")
        logger.info("Scissors detection has been improved!")

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if self.current_state == "MENU":
                            self.start_countdown()
                    elif event.key == pygame.K_r:
                        self.reset_game()

            self.update_game_state()

            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                self.current_frame = self.process_frame(frame)
                self.create_camera_texture(frame)

            self.draw_scene()

            pygame.display.flip()
            clock.tick(60)

        self.cleanup()

    def cleanup(self):
        if self.camera_texture:
            glDeleteTextures([self.camera_texture])
        self.cap.release()
        pygame.quit()


if __name__ == "__main__":
    game = JankenGame()
    game.run()
