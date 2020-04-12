import sqlite3
import logging

class Database:
    def __init__(self, dbname):
        self.conn = sqlite3.connect(dbname)
        self.cur = self.conn.cursor()

    def init_db(self):
        logging.debug("Initializing Database...")
        sql = '''
        CREATE TABLE IF NOT EXISTS user(
            UID INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        );
        '''
        self.cur.execute(sql)
        sql = '''
        CREATE TABLE IF NOT EXISTS board(
            UID INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            moderator INTERGER NOT NULL
        );
        '''
        self.cur.execute(sql)
        sql = '''
        CREATE TABLE IF NOT EXISTS post(
            UID INTEGER PRIMARY KEY AUTOINCREMENT,
            author INTEGER NOT NULL,
            title TEXT NOT NULL,
            date DATETIME DEFAULT current_timestamp,
            content TEXT NOT NULL,
            board INTERGER NOT NULL
        );
        '''
        self.cur.execute(sql)
        sql = '''
        CREATE TABLE IF NOT EXISTS comment(
            UID INTEGER PRIMARY KEY AUTOINCREMENT,
            author INTEGER NOT NULL,
            post TEXT NOT NULL,
            date DATETIME DEFAULT current_timestamp,
            content TEXT NOT NULL
        );
        '''
        self.cur.execute(sql)
        self.conn.commit()

    ### LOGIN ###
    def get_user(self, username):
        sql = "SELECT UID, password FROM user WHERE username='{}'".format(username)
        result = self.execute(sql).fetchone()
        if result == None:
            return None, None, None
        else:
            return result[0], username, result[1]

    def create_user(self, username, email, password):
        sql = "INSERT INTO user(username, email, password) VALUES('{}', '{}', '{}')".format(username, email, password)
        self.execute(sql)
        logging.info("User {} created.".format(username))

    def delete_user(self, username):
        sql = "DELETE FROM user WHERE username='{}'".format(username)
        self.execute(sql)
        logging.info("User {} deleted.".format(username))

    ### POST ###
    def create_board(self, name, moderator):
        sql = "INSERT INTO board(name, moderator) VALUES('{}', '{}')".format(name, moderator)
        self.execute(sql)
        logging.info("Board {} created.".format(name))

    def create_post(self, author, title, content):
        sql = "INSERT INTO post(author, title, content) VALUES('{}', '{}', '{}')".format(author, title, content)
        self.execute(sql)
        logging.info("Post {} created.".format(title))

    def is_board_exist(self, name):
        sql = "SELECT name FROM board WHERE name='{}'".format(name)
        if self.execute(sql).fetchone() == None:
            return False
        else:
            return True

    def list_board(self, keyword):
        sql = "SELECT board.UID, board.name, user.username FROM board, user WHERE user.UID=board.moderator and board.name LIKE '%{}%'".format(keyword)
        return self.execute(sql).fetchall()

    def list_all_board(self):
        sql = "SELECT board.UID, board.name, user.username FROM board, user WHERE user.UID=board.moderator"
        return self.execute(sql).fetchall()

    def list_post(self, board, keyword):
        sql = '''
        SELECT post.UID, post.title, user.username, post.date  
        FROM post, user, board
        WHERE user.UID=post.author and board.UID=post.board 
        and board.name='{}' and post.title LIKE %{}%
        '''.format(board, keyword)
        return self.execute(sql).fetchall()

    def list_all_post(self, board):
        sql = '''
        SELECT post.UID, post.title, user.username, post.date  
        FROM post, user, board
        WHERE user.UID=post.author and board.UID=post.board 
        and board.name='{}'
        '''.format(board)
        return self.execute(sql).fetchall()

    def read_post(self, post_id):
        sql = "SELECT user.username, post.title, post.date, post.content FROM post, user WHERE post.UID={} and user.UID=post.author".format(post_id)
        post = self.execute(sql).fetchone()
        sql = "SELECT author, content, UID FROM comment WHERE post={} ORDER BY UID".format(post_id)
        comment = self.execute(sql).fetchall()
        return post, comment

    def get_post_owner(self, post_id):
        sql = "SELECT author FROM post WHERE UID={}".format(post_id)
        return self.execute(sql).fetchone()

    def delete_post(self, post_id):
        sql = "DELETE FROM post WHERE UID={}".format(post_id)
        self.execute(sql)

    def update_post_title(self, post_id, title):
        sql = "UPDATE post SET title='{}' WHERE UID={}".format(title, post_id)
        self.execute(sql)

    def update_post_content(self, post_id, content):
        sql = "UPDATE post SET content='{}' WHERE UID={}".format(content, post_id)
        self.execute(sql)

    def comment(self, post_id, user, comment):
        sql = "INSERT INTO comment(post, author, content) VALUE('{}', '{}', '{}')".format(post_id, user, comment)
        self.execute(sql)

    ### MISC ###
    def execute(self, sql):
        result = self.cur.execute(sql)
        self.conn.commit()
        return result

    def __del__(self):
        self.conn.close()
