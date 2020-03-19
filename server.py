# -*- coding: utf-8 -*-
import socket
from bbs import *

db = sqlite3.connect("bbs.db")
init_sql = '''CREATE TABLE IF NOT EXISTS users(UID INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL UNIQUE,
email TEXT NOT NULL,
password TEXT NOT NULL);
'''
cursor=db.execute(init_sql)

HOST = '127.0.0.1'
PORT = 8000

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
