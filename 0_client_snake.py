import json
import socket
import threading

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

class Client:

    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.name = input("Enter your name: ")
        self.socket.send(json.dumps({"action" : "log_in", "name" : self.name}).encode("utf-8"))
        self.running = True
        self.playing = False

    def key2str(self, pressed_keys):
        if pressed_keys[K_UP]:
            return "UP"
        if pressed_keys[K_DOWN]:
            return "DOWN"
        if pressed_keys[K_LEFT]:
            return "LEFT"
        if pressed_keys[K_RIGHT]:
            return "RIGHT" 
            
    def game(self):
        while self.playing:
            
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.socket.send(json.dumps({"action" : "quit"}).encode("utf-8"))
                        self.playing = False
                    else:
                        pressed_keys = pygame.key.get_pressed()
                        dr = self.key2str(pressed_keys)
                        self.socket.send(json.dumps({"action" : "turn", "direction" : dr}).encode("utf-8"))
                elif event.type == QUIT:
                    self.socket.send(json.dumps({"action" : "quit"}).encode("utf-8"))
                    self.playing = False
        
        pygame.quit()
        quit()

if __name__ == "__main__":
    client = Client(HOST, PORT)

    while client.running:

        raw_data = client.socket.recv(1024).decode("utf-8")

        i = 0
        while i < len(raw_data):
            j = raw_data.find('}', i)
            data = json.loads(raw_data[i:j + 1])
            i = j + 1        

            if data["action"] == "message":
                print(data["msg"])

            if data["action"] == "initialize":
                SCREEN_WIDTH = data["width"]
                SCREEN_HEIGHT = data["height"]
                BLOCK_SIZE = data["block"]
                client.playing = True
                print("Game initialized!")

                threading.Thread(target = client.game).start()
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))

            if data["action"] == "render":
                #print("data received")

                screen.fill(white)

                surf.fill(red)
                for block in data["p1"]:
                    screen.blit(surf, block)

                surf.fill(blue)
                for block in data["p2"]:
                    screen.blit(surf, block)

                surf.fill(black)
                screen.blit(surf, data["food"])

                pygame.display.update()

            if data["action"] == "quit":
                client.running = False
                client.playing = False
                
    pygame.quit()
    quit()