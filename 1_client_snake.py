import json
import socket
import threading
import random

import pygame
from pygame.locals import *

white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
blue = (0, 0, 255)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLOCK_SIZE = 20

HOST = "xuyufengdeMacBook-Pro.local"
PORT = 12345

pygame.init()

class Snake(pygame.sprite.Sprite):

    def __init__(self, id):
        super().__init__()

        self.length = 4
        bs = BLOCK_SIZE

        self.body = []
        if id == 0:
            for i in range(self.length):
                self.body.append((SCREEN_WIDTH / 2 + i * bs, SCREEN_HEIGHT / 2))
            self.direction = (bs, 0)
        else:
            for i in range(1, self.length + 1):
                self.body.append((SCREEN_WIDTH / 2 - i * bs, SCREEN_HEIGHT / 2))
            self.direction = (-bs, 0)
        self.head = self.body[-1]

        self.eat_food = False

    def die(self):
        bs = BLOCK_SIZE
        n = len(self.body)
        hd = self.head
        if hd[0] < 0 or hd[0] > SCREEN_WIDTH - bs or hd[1] < 0 or hd[1] > SCREEN_HEIGHT - bs:
            return True
        elif hd in self.body[:n - 1]:
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

    def turn(self, dr):
        bs = BLOCK_SIZE
        if dr == "UP":
            self.direction = (0, -bs)
        if dr == "DOWN":
            self.direction = (0, bs)
        if dr == "LEFT":
            self.direction = (-bs, 0)
        if dr == "RIGHT":
            self.direction = (bs, 0)

    def update(self):
        if self.eat_food == False:
            self.body.pop(0)
        else:
            self.eat_food = False
            self.length += 1
        hd = self.head
        dr = self.direction
        self.body.append((hd[0] + dr[0], hd[1] + dr[1]))
        self.head = self.body[-1]

snakes = [Snake(0), Snake(1)]

class Client:

    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.name = input("Enter your name: ")
        self.socket.send(json.dumps({"action" : "log_in", "name" : self.name}).encode("utf-8"))
        self.running = True
        self.playing = False

    def recv(self):
        while self.running:

            raw_data = self.socket.recv(1024).decode("utf-8")

            i = 0
            while i < len(raw_data):
                j = raw_data.find('}', i)
                data = json.loads(raw_data[i:j + 1])
                i = j + 1        

                if data["action"] == "message":
                    print(data["msg"])

                if data["action"] == "initialize":
                    print("Game initialized!")
                    self.idx = data["id"]
                    self.food_loc = data["food_loc"]
                    self.playing = True

                if data["action"] == "turn":
                    other_snake.turn(data["direction"])

                if data["action"] == "update_food":
                    self.food_loc = data["food_loc"]

                if data["action"] == "quit":
                    self.running = False
                    self.playing = False

if __name__ == "__main__":
    client = Client(HOST, PORT)                

    threading.Thread(target = client.recv).start()

    while not client.playing:
        pass

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))

    self_snake = snakes[client.idx]
    other_snake = snakes[1 - client.idx]

    clock = pygame.time.Clock()

    screen.fill(white)

    while client.playing:

        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    client.socket.send(json.dumps({"action" : "quit"}).encode("utf-8"))
                    client.playing = False
                else:
                    pressed_keys = pygame.key.get_pressed()
                    dr = self_snake.key2str(pressed_keys)
                    if dr is not None:
                        self_snake.turn(dr)
                        client.socket.send(json.dumps({"action" : "turn", "direction" : dr }).encode("utf-8"))
                    
            elif event.type == QUIT:
                client.socket.send(json.dumps({"action" : "quit"}).encode("utf-8"))
                client.playing = False

        self_snake.update()
        other_snake.update()

        screen.fill(white)

        for snake in snakes:
            if tuple(client.food_loc) in snake.body:
                snake.eat_food = True
                screen.blit(surf, client.food_loc)
                if snake == self_snake:
                    client.socket.send(json.dumps({"action" : "food_eaten"}).encode("utf-8"))
                break
        
        if self_snake.die() or self_snake.head in other_snake.body:
            client.socket.send(json.dumps({"action" : "quit"}).encode("utf-8"))
            clock.tick(1)
            break

        surf.fill(blue)
        for block in self_snake.body:
            screen.blit(surf, block)

        surf.fill(red)
        for block in other_snake.body:
            screen.blit(surf, block)

        surf.fill(black)
        screen.blit(surf, client.food_loc)

        caption = "p1 score: " + str(snakes[0].length - 4) + "   p2 score: " + str(snakes[1].length - 4)
        pygame.display.set_caption(caption)

        pygame.display.update()

        clock.tick(8)

    pygame.quit()
    quit()