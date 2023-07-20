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

food = Food()

class Server:

    def __init__(self, host = "", port = 12345):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(2)
        print("Searching for connections...")

        self.num_players = 0

        self.connections = []
        self.names = {}

        self.playing = False

    def add_client(self, c, name):
        self.num_players += 1

        self.connections.append(c)
        self.names[c] = name

        if self.num_players == 1:
            c.send(json.dumps({"action" : "message", "msg" : "Waiting for another player..."}).encode("utf-8"))
        else:
            self.playing = True
            self.initialize()

    def initialize(self):
        for c in self.connections:
            c.send(json.dumps({"action" : "message", "msg" : "The game will start in 3 seconds!"}).encode("utf-8"))
        time.sleep(1)
        for i in range(3):
            for c in self.connections:
                c.send(json.dumps({"action" : "message", "msg" : str(3 - i)}).encode("utf-8"))
            time.sleep(1)
        time.sleep(1)
        for i in range(len(self.connections)):
            self.connections[i].send(json.dumps({"action" : "initialize", "food_loc" : food.loc, "id" : i}).encode("utf-8"))
            #connection.send(json.dumps({"action" : "initialize"}).encode("utf-8"))

    def recv(self, c):
        while True:
            data = c.recv(1024).decode("utf-8")
            print(data)

            if not data:
                print(self.names[c] + " has logged out")

                self.num_players -= 1

                self.connections.remove(c)
                del self.names[c]
            
                break
            
            data = json.loads(data)
            
            if data["action"] == "turn":
                for conn in self.connections:
                    if conn != c:
                        conn.send(json.dumps({"action" : "turn", "direction" : data["direction"]}).encode("utf-8"))

            if data["action"] == "food_eaten":
                food.update()
                for c in self.connections:
                    c.send(json.dumps({"action" : "update_food", "food_loc" : food.loc}).encode("utf-8"))

            if data["action"] == "quit":
                print(self.names[c] + " has logged out")

                self.num_players -= 1

                self.connections.remove(c)
                del self.names[c]
            
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
    

    



    

