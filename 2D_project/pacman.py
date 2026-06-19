import time
import cv2
import numpy as np
import math
from engine import GraphicsEngine

class Apple:
    def __init__(self, x, y, r=4):
        self.x = x
        self.y = y
        self.r = r
        self.is_eaten = False

    def draw(self, engine):
        if not self.is_eaten:
            apple_shape = engine.create_circle_arc(self.x, self.y, self.r, 0, 360, seed_point=(self.x, self.y), fill_color=(255, 0, 0))
            apple_shape.draw(engine, color = (200, 0, 0))

class Pacman:
    def __init__(self, start_x, start_y, r=10):
        self.x = start_x
        self.y = start_y
        self.r = r
        self.frame_count = 0
        self.mouth_angles = [5, 15, 25, 35, 45, 35, 25, 15]
        self.direction = "RIGHT"
        self.speed = 2

    def move(self):
        if self.direction == "RIGHT":
            self.x += self.speed
        elif self.direction == "UP":
            self.y += self.speed
        elif self.direction == "DOWN":
            self.y -= self.speed
        elif self.direction == "LEFT":
            self.x -= self.speed

    def check_collision(self, apple):
        if not apple.is_eaten:
            dist = math.sqrt((apple.x - self.x)**2 + (apple.y - self.y)**2)
            if dist <= (self.r + apple.r):
                apple.is_eaten = True
                self.r += 2


    def draw(self, engine):
        index = self.frame_count % len(self.mouth_angles)
        base_start = self.mouth_angles[index]
        base_end = 360 - base_start

        if self.direction == "RIGHT":
            offset = 0
            seed_x, seed_y = self.x - 5, self.y
            eye_x, eye_y = self.x, self.y + 5
        elif self.direction == "UP":
            offset = 90
            seed_x, seed_y = self.x, self.y - 5
            eye_x, eye_y = self.x - 5, self.y
        elif self.direction == "DOWN":
            offset = -90
            seed_x, seed_y = self.x, self.y + 5
            eye_x, eye_y = self.x + 5, self.y
        else: # LEFT
            offset = 180
            seed_x, seed_y = self.x + 5, self.y
            eye_x, eye_y = self.x, self.y + 5

        start_angle = base_start + offset
        end_angle = base_end + offset
        body = engine.create_circle_arc(self.x, self.y, self.r, start_angle, end_angle, is_closed=True, seed_point = (seed_x, seed_y), fill_color = (255, 255, 0), is_connect = True)
        body.draw(engine, color = (255, 200, 0))

        eye = engine.create_circle_arc(eye_x, eye_y, 2, 0, 360, is_closed=True, seed_point=(eye_x, eye_y), fill_color=(0, 0, 0))
        eye.draw(engine, color=(0, 0, 0))

        self.frame_count += 1

def generate_pacman_frames():
        engine = GraphicsEngine(800, 600)
        engine.draw_grid()
        wall_color = (139, 69, 19)
        engine.draw_rectangle(-70, 20, 40, 50, color=wall_color)
        engine.boundary_fill(-50, 45, fill_color=wall_color, boundary_color=wall_color)

        engine.draw_rectangle(-70, -60, 40, 40, color=wall_color)
        engine.boundary_fill(-50, -40, fill_color=wall_color, boundary_color=wall_color)

        engine.draw_rectangle(20, 50, 50, 10, color=wall_color)
        engine.boundary_fill(45, 55, fill_color=wall_color, boundary_color=wall_color)

        engine.draw_rectangle(10, -70, 30, 40, color=wall_color) 
        engine.boundary_fill(25, -50, fill_color=wall_color, boundary_color=wall_color)
        engine.bg_layer = engine.image.copy()

        pacman = Pacman(-60, 0, r=10)
        apples = [
        Apple(0, 0, r=4),
        Apple(-10, 40, r=4),
        Apple(60, 30, r=4),
        Apple(50, -25, r=4)
        ]

        while True:
            engine.clear()
        
            if not apples[0].is_eaten:
                pacman.direction = "RIGHT"
            elif not apples[1].is_eaten:
                pacman.direction = "UP"
            elif not apples[2].is_eaten:
                pacman.direction = "RIGHT"
            elif not apples[3].is_eaten:
                pacman.direction = "DOWN"
            else:
                pacman.speed = 0

            pacman.move()
            for apple in apples:
                pacman.check_collision(apple)

            for apple in apples:
                apple.draw(engine)
            pacman.draw(engine)

            cv_image = np.array(engine.image)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
        
            ret, buffer = cv2.imencode('.jpg', cv_image)
            if not ret:
                continue
            
            frame = buffer.tobytes()
            yield (b'--frame\r\n' 
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)

def get_static_grid():
    engine = GraphicsEngine(800, 600)
    engine.draw_grid()
    
    cv_image = np.array(engine.image)
    cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
    ret, buffer = cv2.imencode('.jpg', cv_image)
    return buffer.tobytes()

