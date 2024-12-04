import sqlite3
import os
import time

import scrlib.mlib as lib

class ImgDB:
    def __init__(self):
        lib.check_path("./data/")
        db_exists = os.path.exists(os.path.join("data", "image.db"))
        with sqlite3.connect(os.path.join("data", "image.db")) as db_conn:
            db = db_conn.cursor()

            if not db_exists:
                db.execute(
                    '''CREATE TABLE if not EXISTS sendlog(
                    filename TEXT ,
                    type TEXT,
                    send TEXT,
                    dt TEXT
                    )''')
                db.execute(
                    '''CREATE TABLE if not EXISTS userfavor(
                    user INT,
                    favor TEXT
                    )''')
        
            db_conn.commit()
    def execute(self, sql, params):
        with sqlite3.connect(os.path.join("data", "image.db")) as db_conn:
            db = db_conn.cursor()
            res = db.execute(sql, params)
            db_conn.commit()
        return res
    # 获取近一个月的记录
    def get_sendlog_month(self):
        startdate = time.strftime(
            "%Y-%m-%d", time.localtime(time.time() - 30 * 24 * 3600))
        tmplist = list(self.execute(
                "SELECT filename, type, send FROM sendlog WHERE dt >= ? group by filename, type, send", (startdate,)))
        return tmplist
    
    def insert(self, filename, msg_type, sender, dt):
        self.execute("INSERT INTO sendlog (filename,type,send,dt) VALUES(?,?,?,?)",
                   (filename, msg_type, sender, dt, ))
        
    def addFavor(self, user, filename):
        self.execute(
            "INSERT INTO userfavor (user, favor) VALUES (?, ?)", (user, filename,))
    def delFavor(self, user, filename):
        self.execute(
            "DELETE FROM userfavor WHERE user=? AND favor=?", (user, filename,))
        
    def getFavorList(self, user):
        reslst = list(self.execute(
            "SELECT favor FROM userfavor WHERE user=? GROUP BY favor", (user,)
        ))
        tmplist = []
        for entry in reslst:
            tmplist.append(entry[0])
        return tmplist
