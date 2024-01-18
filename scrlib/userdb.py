import sqlite3
import os
import time

import scrlib.mlib as lib


class UserDB:
    def __init__(self):
        lib.check_path("./data/")
        db_exists = os.path.exists(os.path.join("data", "user.db"))
        with sqlite3.connect(os.path.join("data", "user.db")) as db_conn:
            db = db_conn.cursor()

            if not db_exists:
                db.execute(
                    '''CREATE TABLE if not EXISTS user(
                    userid TEXT PRIMARY KEY,
                    password TEXT,
                    createtime TEXT
                    )''')
            
            db_conn.commit()
    def execute(self, sql, params = ()):
        with sqlite3.connect(os.path.join("data", "user.db")) as db_conn:
            db = db_conn.cursor()
            res = db.execute(sql, params)
            db_conn.commit()
        return res
    def get_all_user(self) -> list:
        tmplist = list(self.execute("SELECT userid, password, createtime FROM user"))
        return tmplist
    def insert(self, user, password):
        ctime = time.strftime("%Y-%m-%d %H:%M:%S")
        self.execute(
            "INSERT INTO user (userid,password,createtime) VALUES(?,?,?)", (user, password, ctime, ))
    def update_password(self, user, password):
        self.execute("UPDATE user SET password=? WHERE user=?", (password, user, ))
