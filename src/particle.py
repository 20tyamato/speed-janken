# src/particle.py
import math
import random
import time
import warnings

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *

warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")


class Particle:
    def __init__(self, x, y, z, color, effect_type="normal"):
        self.x = x
        self.y = y
        self.z = z
        self.effect_type = effect_type

        if effect_type == "win":
            self.vx = random.uniform(-0.5, 0.5)
            self.vy = random.uniform(1.0, 3.0)
            self.vz = random.uniform(-0.5, 0.5)
            self.color = (1.0, 0.8, 0.0)  # Gold color
            self.size = random.uniform(0.1, 0.25)
            self.sparkle = True
        elif effect_type == "lose":
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.0, 3.0)
            self.vx = math.cos(angle) * speed
            self.vy = random.uniform(-1.0, 1.0)
            self.vz = math.sin(angle) * speed
            self.color = (1.0, 0.2, 0.1)  # Red
            self.size = random.uniform(0.08, 0.2)
            self.sparkle = False
        elif effect_type == "draw":
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0.5, 2.0)
            self.vx = math.cos(angle) * radius
            self.vy = random.uniform(-0.3, 0.3)
            self.vz = math.sin(angle) * radius
            self.color = (0.2, 0.6, 1.0)  # Blue
            self.size = random.uniform(0.05, 0.15)
            self.sparkle = False
        elif effect_type == "countdown":
            self.vx = random.uniform(-1.0, 1.0)
            self.vy = random.uniform(-1.0, 1.0)
            self.vz = random.uniform(-1.0, 1.0)
            self.color = (0.8, 0.8, 0.8)  # White
            self.size = random.uniform(0.03, 0.1)
            self.sparkle = False
        else:
            self.vx = random.uniform(-0.5, 0.5)
            self.vy = random.uniform(-0.5, 0.5)
            self.vz = random.uniform(-0.5, 0.5)
            self.color = color
            self.size = random.uniform(0.05, 0.15)
            self.sparkle = False

        self.life = 1.0
        self.decay = random.uniform(0.005, 0.02)
        self.gravity = -0.02 if effect_type == "win" else 0.02
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        self.life -= self.decay
        self.vy -= self.gravity
        self.rotation += self.rot_speed
        if self.sparkle:
            self.vx += random.uniform(-0.05, 0.05)
            self.vz += random.uniform(-0.05, 0.05)
        return self.life > 0

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 1, 1, 0)

        alpha = self.life
        if self.sparkle:
            sparkle_factor = (math.sin(time.time() * 10 + self.x) + 1) * 0.5
            glColor4f(
                self.color[0] * (0.5 + sparkle_factor * 0.5),
                self.color[1] * (0.5 + sparkle_factor * 0.5),
                self.color[2] * (0.5 + sparkle_factor * 0.5),
                alpha,
            )
        else:
            glColor4f(self.color[0], self.color[1], self.color[2], alpha)

        if self.effect_type == "win":
            glBegin(GL_TRIANGLES)
            s = self.size
            for i in range(5):
                angle1 = i * 72 * math.pi / 180
                angle2 = (i + 0.5) * 72 * math.pi / 180
                angle3 = (i + 1) * 72 * math.pi / 180

                x1 = math.cos(angle1) * s
                y1 = math.sin(angle1) * s
                x2 = math.cos(angle2) * s * 0.5
                y2 = math.sin(angle2) * s * 0.5
                x3 = math.cos(angle3) * s
                y3 = math.sin(angle3) * s

                glVertex3f(0, 0, 0)
                glVertex3f(x1, y1, 0)
                glVertex3f(x2, y2, 0)

                glVertex3f(0, 0, 0)
                glVertex3f(x2, y2, 0)
                glVertex3f(x3, y3, 0)
            glEnd()
        else:
            glBegin(GL_QUADS)
            s = self.size
            faces = [
                [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)],  # Front
                [(-s, -s, -s), (-s, s, -s), (s, s, -s), (s, -s, -s)],  # Back
                [(-s, s, -s), (-s, s, s), (s, s, s), (s, s, -s)],  # Top
                [(-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s)],  # Bottom
                [(s, -s, -s), (s, s, -s), (s, s, s), (s, -s, s)],  # Right
                [(-s, -s, -s), (-s, -s, s), (-s, s, s), (-s, s, -s)],  # Left
            ]
            for face in faces:
                for vertex in face:
                    glVertex3f(*vertex)
            glEnd()

        glPopMatrix()


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.max_particles = 1000

    def add_particle(self, x, y, z, color, effect_type="normal"):
        if len(self.particles) < self.max_particles:
            self.particles.append(Particle(x, y, z, color, effect_type))

    def add_effect(self, effect_type, count=50):
        for _ in range(count):
            x = random.uniform(-8, 8)
            y = random.uniform(-6, 6)
            z = random.uniform(-3, 3)
            self.add_particle(x, y, z, (1, 1, 1), effect_type)

    def clear_particles(self):
        self.particles = []

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        for particle in self.particles:
            particle.draw()

        glDisable(GL_BLEND)
