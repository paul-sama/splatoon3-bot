import csv
import sqlite3
from pathlib import Path
from typing import Union

DATABASE = Path() / "data" / "image"

class ImageManager:
    _has_init = False

    def __init__(self):
        if not ImageManager._has_init:
            if not DATABASE.exists():
                DATABASE.mkdir(parents=True)
                self.database_path = DATABASE / "image.db"
                self.conn = sqlite3.connect(self.database_path)
                self._create_table()
            else:
                self.database_path = DATABASE / "image.db"
                self.conn = sqlite3.connect(self.database_path)
            print("图片数据库连接！")

    def close(self):
        self.conn.close()
        print("图片数据库关闭")

    def _create_table(self):
        c = self.conn.cursor()
        c.execute("""CREATE TABLE IMAGE_DATA(
                    ID CHAR(30) PRIMARY KEY UNIQUE ,
                    IMAGE BLOB
                );""")
        self.conn.commit()

    def add_or_modify(self, name: str, image):
        sql = f"select * from IMAGE_DATA where ID=?"
        c = self.conn.cursor()
        c.execute(sql, (name,))
        data = c.fetchone()
        if not data:  # create user
            sql = f"INSERT INTO IMAGE_DATA (IMAGE, ID) VALUES (?, ?);"
        else:
            sql = f"UPDATE IMAGE_DATA set IMAGE=? where ID=?"
            name = data[0]

        c.execute(sql, (image, name))
        self.conn.commit()

    # return value: visible_fc, visible_card, fc_code, card
    def get_info(self, name) -> []:
        sql = f"select ID, IMAGE from IMAGE_DATA where ID=?"
        c = self.conn.cursor()
        c.execute(sql, (name,))
        data = c.fetchone()
        self.conn.commit()
        return data
