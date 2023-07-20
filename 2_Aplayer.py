import json
import random
import socket
import sys
import threading
import time

import pygame
from pygame.locals import *

HOST = ""
PORT = 12345

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SALMON = (250, 128, 114)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLOCK_SIZE = 20

pygame.init()

pygame.mixer.init()

class Snake(pygame.sprite.Sprite):

    def __init__(self, idx):
        super().__init__()
        self.body = []
        self.length = 4
        bs = BLOCK_SIZE
        if idx == 0:
            for i in range(self.length):
                self.body.append((SCREEN_WIDTH / 2 + i * bs, SCREEN_HEIGHT / 2))
            self.direction = (bs, 0)
            self.color = BLUE
        if idx == 1:
            for i in range(1, self.length + 1):
                self.body.append((SCREEN_WIDTH / 2 - i * bs, SCREEN_HEIGHT / 2))
            self.direction = (-bs, 0)
            self.color = RED
        self.head = self.body.pop()
        
        self.eat_food = False

    def die(self, other):
        hd = self.head
        bs = BLOCK_SIZE
        if hd[0] < 0 or hd[0] > SCREEN_WIDTH - bs or hd[1] < 0 or hd[1] > SCREEN_HEIGHT - bs:
            return True
        elif hd in self.body:
            return True
        elif hd in other.body + [other.head]:
            return True
        return False

    def key2str(self, pressed_keys):
        bs = BLOCK_SIZE
        if pressed_keys[K_UP] and self.direction != (0, bs):
            return "UP"
        if pressed_keys[K_DOWN] and self.direction != (0, -bs):
            return "DOWN"
        if pressed_keys[K_LEFT] and self.direction != (bs, 0):
            return "LEFT"
        if pressed_keys[K_RIGHT] and self.direction != (-bs, 0):
            return "RIGHT"
        return None

    def turn(self, key_str):
        bs = BLOCK_SIZE
        if key_str == "UP" :
            self.direction = (0, -bs)
        if key_str == "DOWN":
            self.direction = (0, bs)
        if key_str == "LEFT":
            self.direction = (-bs, 0)
        if key_str == "RIGHT":
            self.direction = (bs, 0)

    def update(self):
        if self.eat_food == False:
            self.body.pop(0)
        else:
            self.eat_food = False
            self.length += 1
        dr = self.direction
        hd = self.head
        self.body.append(hd)
        self.head = (hd[0] + dr[0], hd[1] + dr[1])

self_snake = Snake(0)
other_snake = Snake(1)
snakes = [self_snake, other_snake]

class Food(pygame.sprite.Sprite):
    
    def __init__(self):
        super().__init__()
        bs = BLOCK_SIZE
        self.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.range = (SCREEN_WIDTH // 2 // bs, SCREEN_HEIGHT // 2 // bs)
        c = self.center
        r = self.range
        self.loc = (c[0] + random.randint(-r[0]+ 1, r[0] - 2) * bs, c[1] + random.randint(-r[1] + 1, r[1] - 2) * bs)

    def update(self, loc = None):
        c = self.center
        r = self.range
        bs = BLOCK_SIZE
        if loc is not None:
            self.loc = loc
        else:
            self.loc = (c[0] + random.randint(-r[0]+ 1, r[0] - 2) * bs, c[1] + random.randint(-r[1] + 1, r[1] - 2) * bs)

food = Food()

def game_loop(c):

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
    bs = BLOCK_SIZE
    surf = pygame.Surface((bs, bs))

    # to run on your computer's terminal
    pygame.mixer.music.load("Play.mp3")
    die_sound = pygame.mixer.Sound("Die.mp3")

    # to run on the vscode terminal
    #pygame.mixer.music.load("asymmetric model/Play.mp3")
    #die_sound = pygame.mixer.Sound("asymmetric model/Die.mp3")

    pygame.mixer.music.play(loops = -1)
        
    playing = True

    while playing:
            
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    c.send(json.dumps({"action" : "quit"}).encode("utf-8"))
                    sys.exit()
                else:
                    pressed_keys = pygame.key.get_pressed()
                    key_str = snake.key2str(pressed_keys)
                    if key_str is not None:
                        c.send(json.dumps({"action" : "turn", "direction" : key_str}).encode("utf-8"))
                        self_snake.turn(key_str)

        if food.loc == self_snake.head:
            self_snake.eat_food = True
            food.update()
            c.send(json.dumps({"action" : "food", "location" : food.loc}).encode("utf-8"))
        
        self_snake.update()
        other_snake.update()

        if self_snake.die(other_snake):
            pygame.mixer.music.pause()
            die_sound.play()

            c.send(json.dumps({"action" : "quit"}).encode("utf-8"))

            time.sleep(2)
            sys.exit()

        screen.fill(WHITE)

        for snake in snakes:
            surf.fill(snake.color)
            for loc in snake.body + [snake.head]:
                screen.blit(surf, loc)

        surf.fill(BLACK)
        screen.blit(surf, food.loc)

        caption = "Your score: " + str(self_snake.length - 4) + "Opponent's score: " + str(other_snake.length - 4)
        pygame.display.set_caption(caption)

        pygame.display.update()

        time.sleep(0.15) # number of frames

    pygame.quit()
    quit()

def recv(c):
    raw_data = c.recv(1024).decode("utf-8")

    i = 0
    while i < len(raw_data):
        j = raw_data.find('}', i)
        data = json.loads(raw_data[i:j + 1])
        i = j + 1   

        if data["action"] == "turn":
            other_snake.turn(data["direction"])

        if data["action"] == "food":
            food.loc = data["location"]

        if data["action"] == "end":
            sys.exit()

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    print("Waiting for another player to join...")

    c, _ = sock.accept()
    threading.Thread(target = recv, args = (c, )).start()
    print("The game will start in 3 seconds!")
    time.sleep(1)
    for i in range(3, 0, -1):
        print(i)
        time.sleep(1)
    print("Game starts!")
    c.send(json.dumps({"action" : "food", "location" : food.loc}).encode("utf-8"))
    
    game_loop(c)