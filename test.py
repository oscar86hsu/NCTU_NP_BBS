import unittest
import multiprocessing
import socket

def start_server():
    import server

class BasicLoginTest(unittest.TestCase):
    # def setUp(self):
    #     self.server = multiprocessing.Process(target=start_server)
    #     self.server.start()

    # def tearDown(self):
    #     self.server.terminate()

    def test_connect(self):
        s = socket.socket()
        s.connect(("127.0.0.1", 3000))
        raw_message = s.recv(1024)
        print(str(raw_message, encoding='utf-8'))
        raw_message = s.recv(1024)
        print(str(raw_message, encoding='utf-8'))
        s.send(b'exit')

if __name__ == "__main__":
    unittest.main()