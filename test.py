import os
import unittest
import socket
import time
import threading
import server
from db import Database

HOST = "127.0.0.1"
PORT = 6000

class ConnectionTest(unittest.TestCase):
    @classmethod    
    def setUpClass(cls):
        test_server = server.BBS_Server(HOST, PORT, "test_connection.db")
        t = threading.Thread(target=test_server.start_listening, args=(), daemon=True)
        t.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        os.remove("test_connection.db")

    def connect(self):
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

class BasicLoginTest(unittest.TestCase):
    @classmethod    
    def setUpClass(cls):
        dbname = "test_login.db"
        test_server = server.BBS_Server(HOST, PORT, dbname)
        t = threading.Thread(target=test_server.start_listening, args=(), daemon=True)
        t.start()
        time.sleep(0.1)
        db = Database(dbname)
        db.create_user('exist_user', 'exist_email', 'exist_password')

    @classmethod
    def tearDownClass(cls):
        os.remove("test_login.db")

    def connect(self):
        s = socket.socket()
        s.connect((HOST, PORT))
        raw_message = s.recv(1024)
        return s

    def test_register_command_fail(self):
        s = self.connect()
        s.send("register\r\n".encode())
        time.sleep(0.1)
        raw_message = s.recv(1024)
        self.assertIn(b'Usage: register <username> <email> <password>\n', raw_message)
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


if __name__ == "__main__":
    unittest.main(buffer=True)