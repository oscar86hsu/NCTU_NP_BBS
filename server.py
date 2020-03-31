# -*- coding: utf-8 -*-
import socket
import sys
import sqlite3

class Exit(Exception):
    pass
class BBS():
    def __init__(self, server):
        super().__init__()
        self.conn, self.addr = server.accept()
        print("New connection.")
        welcome_message = "\n********************************\n** Welcome to the BBS server. **\n********************************\n"
        self.conn.sendall(welcome_message.encode())
        self.login = False

    def wait(self):
        while True:
            try:
                self.conn.sendall('% '.encode())
                raw_client_message = self.conn.recv(1024)
                if raw_client_message == b'\xff\xf4\xff\xfd\x06':
                    self.exit([])
                else:
                    client_message = str(raw_client_message, encoding='utf-8').replace("\r\n", "").split(" ")
                    if client_message[0] == "register":
                        self.register(client_message[1:])
                    elif client_message[0] == "login":
                        self.login(client_message[1:])
                    elif client_message[0] == "logout":
                        self.logout(client_message[1:])
                    elif client_message[0] == "whoami":
                        self.whoami(client_message[1:])
                    elif client_message[0] == "exit":
                        self.exit(client_message[1:])
                    elif client_message[0] == "echo":
                        self.echo(client_message[1:])
                    else:
                        self.unknown()
            except Exit:
                raise Exit()
            except Exception as e:
                print(e)

    def register(self, client_message):
        if len(client_message) != 3:
            message = "Usage: register <username> <email> <password>\n"
            self.conn.sendall(message.encode())
            return

        db = sqlite3.connect("bbs.db")
        sql = "SELECT UID FROM users WHERE username={}".format(client_message[0])
        cursor=db.execute(sql)
        if len(cursor.fetchall()) > 0:
            message = "Username is already used.\n"
            self.conn.sendall(message.encode())
            return

        sql = "INSERT INTO users(username, email, password) VALUES({}, {}, {})".format(client_message[0], client_message[1], client_message[2])
        db.execute(sql)
        message = "Register successfully.\n"
        self.conn.sendall(message.encode())
        return

    def login(self, client_message):
        if len(client_message) != 2:
            message = "Usage: login <username> <password>\n"
            self.conn.sendall(message.encode())
            return
        
        if self.login:
            message = "Please logout first.\n"
            self.conn.sendall(message.encode())
            return

        db = sqlite3.connect("bbs.db")
        sql = "SELECT password FROM users WHERE username={}".format(client_message[0])
        cursor = db.execute(sql)
        data = cursor.fetchone()
        if (data == None) or (data[0] != client_message[1]):
            message = "Login failed.\n"
            self.conn.sendall(message.encode())
            return

        message = "Welcome, {}.\n".format(client_message[0])
        self.conn.sendall(message.encode())
        self.login = True
        self.username = client_message[0]
        return
        
    def logout(self, client_message):
        if len(client_message) > 1:
            message = "Usage: logout\n"
            self.conn.sendall(message.encode())
            return

        if not self.login:
            message = "Please login first.\n"
            self.conn.sendall(message.encode())
            return

        message = "Bye, {}.".format(self.username)
        self.login = False
        del self.username
        self.conn.sendall(message.encode())
        return
        
    
    def whoami(self, client_message):
        if len(client_message) < 1:
            message = "Usage: echo <message>\n"
            self.conn.sendall(message.encode())
            return

        if not self.login:
            message = "Please login first.\n"
            self.conn.sendall(message.encode())
            return

        message = self.username
        self.conn.sendall(message.encode())
        return

    def exit(self, client_message):
        if len(client_message) > 1:
            message = "Usage: exit\n"
            self.conn.sendall(message.encode())
        raise Exit()

    def echo(self, client_message):
        if len(client_message) < 1:
            message = "Usage: echo <message>\n"
        else:
            message = ""
            for m in client_message:
                message += m + " "
            message = message[:-1] + "\n"
        self.conn.sendall(message.encode())
    
    def unknown(self):
        message = "Unknown Command\n"
        self.conn.sendall(message.encode())

    def __del__(self):
        print("Connection Closed")
        self.conn.close()

db = sqlite3.connect("bbs.db")
init_sql = '''CREATE TABLE IF NOT EXISTS users(UID INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL UNIQUE,
email TEXT NOT NULL,
password TEXT NOT NULL);
'''
cursor=db.execute(init_sql)

HOST = ''
if len(sys.argv) > 1:
    PORT = int(sys.argv[1])
else:
    PORT = 3000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(10)
print('Server Started')

while True:
    try:
        bbs = BBS(server)
        bbs.wait()
    except Exit:
        del bbs
