import json
import random
import socket
import threading
import time

HOST = ""
PORT = 12345

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLOCK_SIZE = 20

class Snake():

    def __init__(self, id):

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
        hd = self.head
        if hd[0] < 0 or hd[0] > SCREEN_WIDTH - bs or hd[1] < 0 or hd[1] > SCREEN_HEIGHT - bs:
            return True
        elif hd in self.body:
            return True
        return False

    def turn(self, dr):
        bs = BLOCK_SIZE
        if dr == "UP" and self.direction != (0, bs):
            self.direction = (0, -bs)
        if dr == "DOWN" and self.direction != (0, -bs):
            self.direction = (0, bs)
        if dr == "LEFT" and self.direction != (bs, 0):
            self.direction = (-bs, 0)
        if dr == "RIGHT" and self.direction != (-bs, 0):
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

class Food():
    
    def __init__(self):
        bs = BLOCK_SIZE
        self.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.range = (int(SCREEN_WIDTH / 2) // bs, int(SCREEN_HEIGHT / 2) // bs)
        c = self.center
        r = self.range
        self.loc = (c[0] + random.randint(-r[0]+ 1, r[0] - 2) * bs, c[1] + random.randint(-r[1] + 1, r[1] - 2) * bs)

    def update(self):
        c = self.center
        r = self.range
        bs = BLOCK_SIZE
        self.loc = (c[0] + random.randint(-r[0]+ 1, r[0] - 2) * bs, c[1] + random.randint(-r[1] + 1, r[1] - 2) * bs)

class Server:

    def __init__(self, host = "", port = 12345):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(2)
        print("Searching for connections...")

        self.num_players = 0

        self.connections = []
        self.names = {}
        self.msgs = {}
        self.snakes = {}

        self.playing = False

    def add_client(self, c, name):
        self.num_players += 1

        self.connections.append(c)
        self.names[c] = name
        self.msgs[c] = ''
        self.snakes[c] = []

        #if self.num_players >= 2:
        #    threading.Thread(target = server.synchronize).start()

        if self.num_players == 1:
            c.send(json.dumps({"action" : "message", "msg" : "Waiting for another player..."}).encode("utf-8"))
        else:
            self.playing = True
            self.initialize()

    def synchronize(self):
        while self.num_players >= 2:
            for connection in self.connections:
                connection.send(json.dumps({"action" : "message", "msg" : "synchronizing...\n" + self.msgs[connection]}).encode("utf-8"))
            time.sleep(1)

    def initialize(self):
        for c in self.connections:
            c.send(json.dumps({"action" : "message", "msg" : "The game will start in 3 seconds!"}).encode("utf-8"))
        time.sleep(1)
        for i in range(3):
            for c in self.connections:
                c.send(json.dumps({"action" : "message", "msg" : str(3 - i)}).encode("utf-8"))
            time.sleep(1)
        time.sleep(1)
        for c in self.connections:
            c.send(json.dumps({"action" : "initialize", "width" : SCREEN_WIDTH, "height" : SCREEN_HEIGHT, "block" : BLOCK_SIZE}).encode("utf-8"))
            #connection.send(json.dumps({"action" : "initialize"}).encode("utf-8"))

        p1 = Snake(0)
        self.snakes[self.connections[0]] = p1
        p2 = Snake(1)
        self.snakes[self.connections[1]] = p2
        self.food = Food()

        threading.Thread(target = server.game).start()

    def game(self):
        
        while True:
            for snake in self.snakes.values():
                snake.update()
                
            s1, s2 = self.snakes.values()
            food = self.food
                
            for c in self.connections:
                c.send(json.dumps({"action" : "render", "p1" : s1.body, "p2" : s2.body, "food" : food.loc}).encode("utf-8"))
                #c.send(json.dumps({"action" : "render", "p1" : 400, "p2" : 380, "food" : 400}).encode("utf-8"))
                #c.send(json.dumps({"action" : "render"}).encode("utf-8"))

            time.sleep(1)

    def recv(self, c):
        while True:
            data = c.recv(1024).decode("utf-8")
            print(data)

            if not data:
                print(self.names[c] + " has logged out")

                self.num_players -= 1

                self.connections.remove(c)
                del self.names[c]
                del self.msgs[c]
                del self.snakes[c]
            
                break
            
            data = json.loads(data)

            if data["action"] == "update":
                self.msgs[c] = data["msg"]
            
            if data["action"] == "turn":
                self.snakes[c].turn(data["direction"])

            if data["action"] == "quit":
                print(self.names[c] + " has logged out")

                self.num_players -= 1

                self.connections.remove(c)
                del self.names[c]
                del self.msgs[c]
                del self.snakes[c]
            
                for c in self.connections:
                    c.send(json.dumps({"action" : "quit"}).encode("utf-8"))

    def run(self):

        while True:
            
            c, addr = self.socket.accept()

            data = c.recv(1024).decode("utf-8")
            data = json.loads(data)

            print(data["name"] + " has logged in")
            self.add_client(c, data["name"])

            threading.Thread(target = self.recv, args = (c, )).start()

if __name__ == "__main__":
    server = Server(HOST, PORT)
    threading.Thread(target = server.run).start()
    

    



    

