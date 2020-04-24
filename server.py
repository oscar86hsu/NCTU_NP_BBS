# -*- coding: utf-8 -*-
import socket
import sys
import threading
import logging
from db import Database

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

    def get_userid(self):
        return self.uid


class BBS_Server:
    def __init__(self, host, port, dbname = "bbs.db"):
        logging.debug("Initializing Server...")
        super().__init__()
        self.host = host
        self.port = port
        self.dbname = dbname
        db = Database(self.dbname)
        logging.debug("Database name: {}".format(self.dbname))
        db.init_db()

    def start_listening(self):
        self.sock = socket.socket()
        self.sock.bind((self.host, self.port))
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.sock.listen(50)
        logging.info("Start listening at port {}".format(self.port))
        print("Start listening at port {}".format(self.port))

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
        client.set_login_stat(False)
        while True:
            try:
                self.command_handler(client)
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
        logging.debug("Welcome message sent!")

    def command_handler(self, client):
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
                    elif client_message[0] == "create-board":
                        self.create_board(client, client_message[1:])
                    elif client_message[0] == "create-post":
                        self.create_post(client, client_message[1:])
                    elif client_message[0] == "list-board":
                        self.list_board(client, client_message[1:])
                    elif client_message[0] == "list-post":
                        self.list_post(client, client_message[1:])
                    elif client_message[0] == "read":
                        self.read(client, client_message[1:])
                    elif client_message[0] == "delete-post":
                        self.delete_post(client, client_message[1:])
                    elif client_message[0] == "update-post":
                        self.update_post(client, client_message[1:])
                    elif client_message[0] == "comment":
                        self.comment(client, client_message[1:])
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

        db = Database(self.dbname)
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

        db = Database(self.dbname)
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
    def create_board(self, client, client_message):
        if (len(client_message) < 1) or (len(client_message) > 2):
            message = "Usage: create-board <name>\n"
            client.conn.sendall(message.encode())
            return

        if not client.get_login_stat():
            message = "Please login first.\n"
            client.conn.sendall(message.encode())
            return

        db = Database(self.dbname)
        if db.is_board_exist(client_message[0]):
            message = "Board already exist.\n"
            client.conn.sendall(message.encode())
            return

        db.create_board(client_message[0], client.get_userid())
        logging.info("Board {} created.".format(client_message[0]))
        message = "Create board successfully.\n"
        client.conn.sendall(message.encode())
        return

    def create_post(self, client, client_message):
        if len(client_message) < 1:
            message = "Usage: create-post <board-name> --title <title> --content <content>\n"
            client.conn.sendall(message.encode())
            return
        elif client_message[0] == "--title" or client_message[0] == "--content":
            message = "Usage: create-post <board-name> --title <title> --content <content>\n"
            client.conn.sendall(message.encode())
            return
        
        if not client.get_login_stat():
            message = "Please login first.\n"
            client.conn.sendall(message.encode())
            return

        try:
            title_index = client_message.index("--title")
        except ValueError:
            message = "Usage: create-post <board-name> --title <title> --content <content>\n"
            client.conn.sendall(message.encode())
            return

        try:
            content_index = client_message.index("--content")
        except ValueError:
            message = "Usage: create-post <board-name> --title <title> --content <content>\n"
            client.conn.sendall(message.encode())
            return

        db = Database(self.dbname)
        if not db.is_board_exist(client_message[0]):
            message = "Board does not exist.\n"
            client.conn.sendall(message.encode())
            return

        title = ""
        content = ""
        tmp = ""

        while title_index < (len(client_message) - 1):
            title_index += 1
            tmp = client_message[title_index]
            if tmp == "--content":
                break
            title += client_message[title_index] + " "

        tmp = ""
        while content_index < (len(client_message) - 1):
            content_index += 1
            tmp = client_message[content_index]
            if tmp == "--title":
                break
            content += client_message[content_index] + " "

        title = title[:-1]
        content = content[:-1]
        if len(title) == 0:
            message = "Title cannot be empty!\n"
            client.conn.sendall(message.encode())
            return

        db.create_post(client.get_userid(), title, content, client_message[0])
        logging.info("Post {} created.".format(title))
        message = "Create post successfully.\n"
        client.conn.sendall(message.encode())

    def list_board(self, client, client_message):
        if len(client_message) > 2:
            message = "Usage: list-board (##<key>)\n"
            client.conn.sendall(message.encode())
            return

        if len(client_message) < 1:
            db = Database(self.dbname)
            boards = db.list_all_board()
        elif client_message[0].startswith("##"):
            db = Database(self.dbname)
            boards = db.list_board(client_message[0][2:])
        else:
            message = "Usage: list-board (##<key>)\n"
            client.conn.sendall(message.encode())
            return
        
        if len(boards) == 0:
            message = "There's no board yet\n"
            client.conn.sendall(message.encode())
            return

        message = "{:10}{:15}{:15}\n".format("Index", "Name", "Moderator")
        client.conn.sendall(message.encode())
        for board in boards:
            message = "{:10}{:15}{:15}\n".format(str(board[0]), board[1], board[2])
            client.conn.sendall(message.encode())


    def list_post(self, client, client_message):
        if len(client_message) > 3:
            message = "Usage: list-post <board-name> (##<key>)\n"
            client.conn.sendall(message.encode())
            return
        elif len(client_message) == 0:
            message = "Usage: list-post <board-name> (##<key>)\n"
            client.conn.sendall(message.encode())
            return

        db = Database(self.dbname)
        if not db.is_board_exist(client_message[0]):
            message = "Board does not exist.\n"
            client.conn.sendall(message.encode())
            return

        if len(client_message) < 2:
            db = Database(self.dbname)
            posts = db.list_all_post(client_message[0])
        elif client_message[1].startswith("##"):
            db = Database(self.dbname)
            posts = db.list_post(client_message[0], client_message[1][2:])
        else:
            message = "Usage: list-post <board-name> (##<key>)\n"
            client.conn.sendall(message.encode())
            return

        message = "{:8}{:12}{:12}{:12}\n".format("ID", "Title", "Author", "Date")
        client.conn.sendall(message.encode())
        for post in posts:
            message = "{:8}{:12}{:12}{:12}\n".format(str(post[0]), post[1], post[2], post[3])
            client.conn.sendall(message.encode())

    def read(self, client, client_message):
        if len(client_message) != 1:
            message = "Usage: read <post-id>\n"
            client.conn.sendall(message.encode())
            return

        db = Database(self.dbname)
        post, comments = db.read_post(client_message[0])

        if post == None:
            message = "Post does not exist.\n"
            client.conn.sendall(message.encode())
            return

        message =  "Author   : " + post[0] + "\n"
        message += "Title    : " + post[1] + "\n"
        message += "Date     : " + post[2] + "\n"
        message += "--\n"
        message += post[3].replace("<br>", "\n") + "\n"
        message += "--\n"
        client.conn.sendall(message.encode())
        for comment in comments:
            message = comment[0] + " : " + comment[1]
            client.conn.sendall(message.encode())
            
        
    def delete_post(self, client, client_message):
        if len(client_message) != 1:
            message = "Usage: delete-post <post-id>\n"
            client.conn.sendall(message.encode())
            return

        if not client.get_login_stat():
            message = "Please login first.\n"
            client.conn.sendall(message.encode())
            return

        db = Database(self.dbname)
        author = db.get_post_owner(client_message[0])
        if author == None:
            message = "Post does not exist.\n"
            client.conn.sendall(message.encode())
            return

        if author != client.get_userid():
            message = "You are not the post owner.\n"
            client.conn.sendall(message.encode())
            return

        db.delete_post(client_message[0])

    def update_post(self, client, client_message):
        if len(client_message) < 3:
            message = "Usage: update-post <post-id> --title/content <new>\n"
            client.conn.sendall(message.encode())
            return

        if not client.get_login_stat():
            message = "Please login first.\n"
            client.conn.sendall(message.encode())
            return

        db = Database(self.dbname)
        author = db.get_post_owner(client_message[0])
        if author == None:
            message = "Post does not exist.\n"
            client.conn.sendall(message.encode())
            return

        if author != client.get_userid():
            message = "You are not the post owner.\n"
            client.conn.sendall(message.encode())
            return

        if client_message[2] == "--title":
            title = ""
            index = 2
            while index < len(client_message):
                title += client_message[index]
                index += 1
            db.update_post_title(client_message[0], title)
        elif client_message[2] == "--content":
            content = ""
            index = 2
            while index < len(client_message):
                content += client_message[index]
                index += 1
            db.update_post_content(client_message[0], content)
        else:
            message = "Usage: update-post <post-id> --title/content <new>\n"
            client.conn.sendall(message.encode())
            return

    def comment(self, client, client_message):
        if len(client_message) < 2:
            message = "Usage: comment <post-id> <comment>\n"
            client.conn.sendall(message.encode())
            return

        if not client.get_login_stat():
            message = "Please login first.\n"
            client.conn.sendall(message.encode())
            return

        db = Database(self.dbname)
        author = db.get_post_owner(client_message[0])
        if author == None:
            message = "Post does not exist.\n"
            client.conn.sendall(message.encode())
            return

        comment = ""
        index = 1
        while index < len(client_message):
            comment += client_message[index]

        db.comment(client_message[0], comment)

    ### MISC ###
    def exit(self, client, client_message):
        if len(client_message) > 1:
            message = "Usage: exit\n"
            client.conn.sendall(message.encode())
        client.conn.close()
        logging.info("Connection Closed, {}".format(client.addr))
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
