import sqlite3
import os

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
                    user TEXT ,
                    password TEXT,
                    dt TEXT
                    )''')
            
            db_conn.commit()