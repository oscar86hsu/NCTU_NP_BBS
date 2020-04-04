# -*- coding: utf-8 -*-
import socket
import sys
import threading
import logging
from db import Database

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

class Exit(Exception):
    pass

class Connection:
    def __init__(self, conn, addr):
        super().__init__()
        self.is_login = False
        self.username = None
        self.uid = -1
        self.conn = conn
        self.addr = addr

    def set_login_stat(self, value):
        self.is_login = value

    def set_username(self, value):
        self.username = value

    def set_userid(self, value):
        self.uid = value

    def get_login_stat(self):
        return self.is_login

    def get_username(self):
        return self.username


class BBS_Server:
    def __init__(self, host, port):
        logging.debug("Initializing Server...")
        super().__init__()
        self.host = host
        self.port = port
        db = Database("bbs.db")
        db.init_db()

    def start_listening(self):
        self.sock = socket.socket()
        self.sock.bind((self.host, self.port))
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.listen(50)
        logging.info("Start listening at port {}".format(self.port))

        while True:
            try:
                conn, addr = self.sock.accept()
                client = Connection(conn, addr)
                t = threading.Thread(target=self.connection_handler, args=(client,), daemon=True)
                t.start()
            except KeyboardInterrupt:
                logging.info("Keyboard Interrupt Exit!")
                self.sock.close()
                exit(0)

    def connection_handler(self, client):
        logging.info("New connection, {}.".format(client.addr))
        print("New connection.")
        self.send_welcome_message(client)
        while True:
            try:
                self.wait(client)
            except Exit:
                logging.info("Connection Closed.")
                del client
                exit(0)
            except BrokenPipeError:
                logging.warning("Broken Pipe.")
                del client
                exit(0)

    def send_welcome_message(self, client):
        welcome_message = "\n********************************\n** Welcome to the BBS server. **\n********************************\n"
        client.conn.sendall(welcome_message.encode())
        client.set_login_stat(False)
        logging.debug("Welcome message sent!")

    def wait(self, client):
        while True:
            try:
                client.conn.sendall('% '.encode())
                raw_client_message = client.conn.recv(1024)
                logging.debug("Raw client message: {}".format(raw_client_message))
                if raw_client_message == b'\xff\xf4\xff\xfd\x06':
                    self.exit(client, [])
                else:
                    client_message = str(raw_client_message, encoding='utf-8').replace("\r\n", "").split(" ")
                    if client_message[0] == "register":
                        self.register(client, client_message[1:])
                    elif client_message[0] == "login":
                        self.login(client, client_message[1:])
                    elif client_message[0] == "logout":
                        self.logout(client, client_message[1:])
                    elif client_message[0] == "whoami":
                        self.whoami(client, client_message[1:])
                    elif client_message[0] == "exit":
                        self.exit(client, client_message[1:])
                    elif client_message[0] == "echo":
                        self.echo(client, client_message[1:])
                    else:
                        self.unknown(client)
            except Exit:
                raise Exit()

    ### LOGIN ###
    def register(self, client, client_message):
        if len(client_message) != 3:
            message = "Usage: register <username> <email> <password>\n"
            client.conn.sendall(message.encode())
            return

        db = Database("bbs.db")
        uid, username, password = db.get_user(client_message[0])
        if  username != None:
            message = "Username is already used.\n"
            client.conn.sendall(message.encode())
            return

        db.create_user(client_message[0], client_message[1], client_message[2])
        message = "Register successfully.\n"
        client.conn.sendall(message.encode())
        return

    def login(self, client, client_message):
        if len(client_message) != 2:
            message = "Usage: login <username> <password>\n"
            client.conn.sendall(message.encode())
            return
        
        if client.get_login_stat():
            message = "Please logout first.\n"
            client.conn.sendall(message.encode())
            return

        db = Database("bbs.db")
        uid, username, password = db.get_user(client_message[0])

        if (username == None) or (password != client_message[1]):
            logging.warning("{} login failed!".format(client_message[0]))
            message = "Login failed.\n"
            client.conn.sendall(message.encode())
            return

        message = "Welcome, {}.\n".format(client_message[0])
        logging.info("{} login successfully!".format(client_message[0]))
        client.conn.sendall(message.encode())
        client.set_login_stat(True)
        client.set_username(client_message[0])
        client.set_userid(uid)
        return
        
    def logout(self, client, client_message):
        if len(client_message) > 1:
            message = "Usage: logout\n"
            client.sendall(message.encode())
            return

        if not client.get_login_stat():
            message = "Please login first.\n"
            client.conn.sendall(message.encode())
            return

        logging.info("{} logout successfully!".format(client.get_username()))
        message = "Bye, {}.\n".format(client.get_username())
        client.set_login_stat(False)
        client.conn.sendall(message.encode())
        return
        
    
    def whoami(self, client, client_message):
        if len(client_message) > 1:
            message = "Usage: whoami\n"
            client.conn.sendall(message.encode())
            return

        if not client.get_login_stat():
            message = "Please login first.\n"
            client.conn.sendall(message.encode())
            return

        message = client.username + ".\n"
        client.conn.sendall(message.encode())
        return

    ### POST ###

    ### MISC ###
    def exit(self, client, client_message):
        if len(client_message) > 1:
            message = "Usage: exit\n"
            client.conn.sendall(message.encode())
        client.conn.close()
        logging.info("Connection Closed, {}".format(client.addr))
        print("Connection Closed")
        raise Exit()

    def echo(self, client, client_message):
        if len(client_message) < 1:
            message = "Usage: echo <message>\n"
        else:
            message = ""
            for m in client_message:
                message += m + " "
            message = message[:-1] + "\n"
        client.conn.sendall(message.encode())
    
    def unknown(self, client):
        message = "Unknown Command\n"
        client.conn.sendall(message.encode())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    else:
        PORT = 3000

    server = BBS_Server('', PORT)
    logging.debug("Server created!")
    server.start_listening()
    del server
