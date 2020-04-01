import sqlite3

class Database:
    def __init__(self, dbname):
        self.conn = sqlite3.connect(dbname)
        self.cur = self.conn.cursor()

    def init_db(self):
        init_sql = '''CREATE TABLE IF NOT EXISTS users(UID INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL,
        password TEXT NOT NULL);
        '''
        self.cur.execute(init_sql)
        self.conn.commit()

    def get_user(self, username):
        sql = "SELECT password FROM users WHERE username='{}'".format(username)
        result = self.execute(sql).fetchone()
        if result == None:
            return None, None
        else:
            return username, result[0]

    def create_user(self, username, email, password):
        sql = "INSERT INTO users(username, email, password) VALUES('{}', '{}', '{}')".format(username, email, password)
        self.execute(sql)

    def execute(self, sql):
        result = self.cur.execute(sql)
        self.conn.commit()
        return result

    def __del__(self):
        self.conn.close()
