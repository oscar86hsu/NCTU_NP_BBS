import os
import glob
import unittest
import socket
import time
import threading
import logging
import server
from db import Database

fileList = glob.glob('*.db')
for filePath in fileList:
    try:
        if filePath == 'bbs.db':
            continue
        os.remove(filePath)
    except OSError:
        print("Error while deleting file")


# logging.basicConfig(level=logging.DEBUG,
#                     format='%(asctime)s [%(levelname)s] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S')

HOST = "127.0.0.1"


class ConnectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        PORT = 6000
        test_server = server.BBS_Server(HOST, PORT, "test_connection.db")
        t = threading.Thread(
            target=test_server.start_listening, args=(), daemon=True)
        t.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        os.remove("test_connection.db")

    def connect(self):
        PORT = 6000
        s = socket.socket()
        s.connect((HOST, PORT))
        raw_message = s.recv(1024)
        time.sleep(1)
        return s

    def test_single_connection(self):
        s = self.connect()
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_multiple_connection(self):
        connections = []
        for i in range(15):
            t = threading.Thread(target=self.test_single_connection, args=())
            t.start()
            connections.append(t)

        for c in connections:
            c.join()


class LoginTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dbname = "test_login.db"
        PORT = 6001
        test_server = server.BBS_Server(HOST, PORT, dbname)
        t = threading.Thread(
            target=test_server.start_listening, args=(), daemon=True)
        t.start()
        time.sleep(0.1)
        db = Database(dbname)
        db.create_user('exist_user', 'exist_email', 'exist_password')

    @classmethod
    def tearDownClass(cls):
        os.remove("test_login.db")

    def connect(self):
        PORT = 6001
        s = socket.socket()
        s.connect((HOST, PORT))
        raw_message = s.recv(1024)
        return s

    def test_register_command_fail(self):
        s = self.connect()
        s.send("register\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(
            b'Usage: register <username> <email> <password>\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_register_fail_user_exist(self):
        s = self.connect()
        s.send("register exist_user exist_email exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Username is already used.\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_register_success(self):
        s = self.connect()
        s.send("register new_user new_email new_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Register successfully.\n', raw_message, )
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_login_command_fail(self):
        s = self.connect()
        s.send("login\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Usage: login <username> <password>\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_login_fail_no_user(self):
        s = self.connect()
        s.send("login user password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Login failed.\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_login_fail_not_logout(self):
        s = self.connect()
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Welcome, exist_user.\n', raw_message)
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Please logout first.\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_login_success(self):
        s = self.connect()
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Welcome, exist_user.\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_logout_fail(self):
        s = self.connect()
        s.send("logout\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Please login first.\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_logout_success(self):
        s = self.connect()
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Welcome, exist_user.\n', raw_message)
        s.send("logout\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Bye, exist_user.\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_whoami_fail(self):
        s = self.connect()
        s.send("whoami\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Please login first.\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_whoami_success(self):
        s = self.connect()
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Welcome, exist_user.\n', raw_message)
        s.send("whoami\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'exist_user.\n', raw_message)
        s.send("exit\r\n".encode())
        s.close()
        del s


class BoardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        PORT = 6002
        dbname = "test_board.db"
        test_server = server.BBS_Server(HOST, PORT, dbname)
        t = threading.Thread(
            target=test_server.start_listening, args=(), daemon=True)
        t.start()
        time.sleep(0.1)
        db = Database(dbname)
        db.create_user('exist_user', 'exist_email', 'exist_password')
        db.create_board('exist_board', '1')
        db.create_board('key_board', '1')

    @classmethod
    def tearDownClass(cls):
        os.remove("test_board.db")

    def connect(self):
        PORT = 6002
        s = socket.socket()
        s.connect((HOST, PORT))
        raw_message = s.recv(1024)
        return s

    def test_create_board_success(self):
        s = self.connect()
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Welcome, exist_user.\n', raw_message)

        s.send("create-board new_board\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Create board successfully.\n', raw_message)

        s.send("exit\r\n".encode())
        s.close()
        del s

        sql = ''' DELETE FROM board WHERE name="new_board" '''
        Database("test_board.db").execute(sql)
        

    def test_create_board_fail_exist(self):
        s = self.connect()
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Welcome, exist_user.\n', raw_message)

        s.send("create-board exist_board\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Board is already exist.\n', raw_message)

        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_create_board_fail_login(self):
        s = self.connect()
        s.send("create-board new_board\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Please login first.\n', raw_message)

        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_create_board_fail_command(self):
        s = self.connect()
        s.send("create-board\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Usage: create-board <name>\n', raw_message)

        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_list_all_board_success(self):
        s = self.connect()
        s.send("list-board\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        header = "{:10}{:15}{:15}\n".format(
            "Index", "Name", "Moderator").encode()
        board_list = "{:10}{:15}{:15}\n".format("1", "exist_board", "exist_user").encode() + "{:10}{:15}{:15}\n".format("2", "key_board", "exist_user").encode()
        self.assertIn(header + board_list, raw_message)

        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_list_key_board_success(self):
        s = self.connect()
        s.send("list-board ##key\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        header = "{:10}{:15}{:15}\n".format(
            "Index", "Name", "Moderator").encode()
        board_list = "{:10}{:15}{:15}\n".format(
            "2", "key_board", "exist_user").encode()
        self.assertIn(header + board_list, raw_message)

        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_list_board_fail_command(self):
        s = self.connect()
        s.send("list-board key\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b"Usage: list-board (##<key>)\n", raw_message)

        s.send("list-board key is exist\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b"Usage: list-board (##<key>)\n", raw_message)

        s.send("exit\r\n".encode())
        s.close()
        del s


class PostTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        PORT = 6003
        dbname = "test_post.db"
        test_server = server.BBS_Server(HOST, PORT, dbname)
        t = threading.Thread(
            target=test_server.start_listening, args=(), daemon=True)
        t.start()
        time.sleep(0.1)
        db = Database(dbname)
        db.create_user('exist_user', 'exist_email', 'exist_password')
        db.create_user('other_user', 'other_email', 'other_password')
        db.create_board('exist_board', '1')
        db.create_post('1', 'exist_post', 'exist_content<br>newline', '1')
        db.create_post('1', 'key_post', 'key_content<br>newline', '1')

    @classmethod
    def tearDownClass(cls):
        os.remove("test_post.db")

    def connect(self):
        PORT = 6003
        s = socket.socket()
        s.connect((HOST, PORT))
        raw_message = s.recv(1024)
        return s

    def test_create_post_success(self):
        s = self.connect()
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Welcome, exist_user.\n', raw_message)

        s.send("create-post exist_board --title test title --content test_content 123 <br> 456 789\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Create post successfully.\n', raw_message)

        sql = ''' SELECT title, content FROM post WHERE title='test title'; '''
        db = Database("test_post.db")
        result = db.execute(sql).fetchall()
        self.assertEqual(len(result), 1)
        self.assertEqual("test title", result[0][0])
        self.assertEqual("test_content 123 <br> 456 789", result[0][1])

        s.send("exit\r\n".encode())
        s.close()
        del s

        sql = ''' DELETE FROM post WHERE title="test title" '''
        db.execute(sql)

    def test_create_post_fail_command(self):
        s = self.connect()
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Welcome, exist_user.\n', raw_message)

        s.send("create-post --title test title --content test_content 123 <br> 456 789\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Usage: create-post <board-name> --title <title> --content <content>\n', raw_message)

        s.send("create-post".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Usage: create-post <board-name> --title <title> --content <content>\n', raw_message)

        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_create_post_fail_login(self):
        s = self.connect()
        s.send("create-post exist_board --title test title --content test_content 123 <br> 456 789\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Please login first.\n', raw_message)

        s.send("exit\r\n".encode())
        s.close()
        del s

    def test_create_post_success(self):
        s = self.connect()
        s.send("login exist_user exist_password\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Welcome, exist_user.\n', raw_message)

        s.send("create-post not_exist_board --title test title --content test_content 123 <br> 456 789\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Board does not exist.\n', raw_message)

        sql = ''' SELECT title, content FROM post WHERE title='test title'; '''
        db = Database("test_post.db")
        result = db.execute(sql).fetchall()
        self.assertEqual(len(result), 0)

        s.send("exit\r\n".encode())
        s.close()
        del s


if __name__ == "__main__":
    unittest.main(buffer=True)

      
