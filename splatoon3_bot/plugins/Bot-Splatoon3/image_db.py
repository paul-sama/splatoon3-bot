import os
import sqlite3
from pathlib import Path

from nonebot.log import logger

from .utils import WeaponData

DATABASE_path = Path(os.path.join(os.path.dirname(__file__), "data", "image"))
DATABASE = Path(DATABASE_path, "image.db")


class ImageDB:
    _has_init = False

    def __init__(self):
        if not ImageDB._has_init:
            if not DATABASE_path.exists():
                DATABASE.mkdir(parents=True)
            self.database_path = DATABASE
            self.conn = sqlite3.connect(self.database_path)
            self._create_table()
            logger.info("图片数据库连接！")

    # 载入插件时，清空合成图片缓存表
    def clean_image_temp(self):
        if DATABASE_path.exists():
            # 数据库文件存在时
            c = self.conn.cursor()
            # 清空合成图片缓存表
            c.execute("delete from IMAGE_TEMP;")
            self.conn.commit()
            logger.info("数据库合成图片缓存数据已清空！")

    # 关闭数据库
    def close(self):
        self.conn.close()
        logger.info("图片数据库关闭")

    # 创建表
    def _create_table(self):
        c = self.conn.cursor()
        # 一次只能执行一条sql语句
        # 创建图片素材数据库
        c.execute(
            """CREATE TABLE IF NOT EXISTS IMAGE_DATA(
                    id INTEGER PRIMARY KEY AUTOINCREMENT ,
                    image_name Char(30) UNIQUE,
                    image_data BLOB,
                    image_zh_name Char(30),
                    image_source_type Char(30)
                );"""
        )
        # 创建合成图片缓存数据库
        c.execute(
            """CREATE TABLE IF NOT EXISTS IMAGE_TEMP(
                    id INTEGER PRIMARY KEY AUTOINCREMENT ,
                    trigger_word Char(30) UNIQUE,
                    image_data BLOB,
                    image_expire_time TEXT
                );"""
        )
        # 创建武器信息数据库
        c.execute(
            """CREATE TABLE IF NOT EXISTS WEAPON_INFO(
                    id INTEGER PRIMARY KEY AUTOINCREMENT ,
                    name Char(30) UNIQUE,
                    sub_name Char(30),
                    special_name Char(30),
                    special_points int,
                    level int,
                    weapon_class Char(30),
                    zh_name Char(30),
                    zh_sub_name Char(30),
                    zh_special_name Char(30)
                );"""
        )
        # 创建武器图片数据库
        c.execute(
            """CREATE TABLE IF NOT EXISTS WEAPON_IMAGES(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name Char(30),
                    type Char(30),
                    image BLOB
                );"""
        )
        # 提交事务
        self.conn.commit()

    # 添加或修改 图片数据表
    def add_or_modify_IMAGE_DATA(
        self, image_name: str, image_data, image_zh_name: str, image_source_type: str
    ):
        sql = f"select * from IMAGE_DATA where image_name=?"
        c = self.conn.cursor()
        c.execute(sql, (image_name,))
        data = c.fetchone()
        if not data:  # create user
            sql = f"INSERT INTO IMAGE_DATA (image_data, image_zh_name,image_source_type,image_name) VALUES (?, ?,?, ?);"
        else:
            sql = f"UPDATE IMAGE_DATA set image_data=?,image_zh_name=?,image_source_type=? where image_name=?"
        c.execute(sql, (image_data, image_zh_name, image_source_type, image_name))
        self.conn.commit()

    # 取图片信息(图片二进制数据)
    # return value: visible_fc, visible_card, fc_code, card
    def get_img_data(self, image_name) -> []:
        sql = f"select image_data,image_zh_name,image_source_type from IMAGE_DATA where image_name=?"
        c = self.conn.cursor()
        c.execute(sql, (image_name,))
        data = c.fetchone()
        self.conn.commit()
        return data

    # 添加或修改 图片缓存表
    def add_or_modify_IMAGE_TEMP(
        self, trigger_word: str, image_data, image_expire_time: str
    ):
        sql = f"select * from IMAGE_TEMP where trigger_word=?"
        c = self.conn.cursor()
        c.execute(sql, (trigger_word,))
        data = c.fetchone()
        if not data:  # create user
            sql = f"INSERT INTO IMAGE_TEMP ( image_data,image_expire_time,trigger_word) VALUES (?, ?, ?);"
        else:
            sql = f"UPDATE IMAGE_TEMP set image_data=?,image_expire_time=? where trigger_word=?"

        c.execute(sql, (image_data, image_expire_time, trigger_word))
        self.conn.commit()

    # 取图片缓存(图片二进制数据)
    # return value: visible_fc, visible_card, fc_code, card
    def get_img_temp(self, trigger_word) -> []:
        sql = (
            f"select image_data,image_expire_time from IMAGE_TEMP where trigger_word=?"
        )
        c = self.conn.cursor()
        c.execute(sql, (trigger_word,))
        data = c.fetchone()
        self.conn.commit()
        return data

    # 添加或修改 武器数据表
    def add_or_modify_weapon_info(self, weapon: WeaponData):
        sql = f"select * from WEAPON_INFO where name=?"
        c = self.conn.cursor()
        c.execute(sql, (weapon.name,))
        data = c.fetchone()
        if not data:  # create user
            sql = (
                f"INSERT INTO WEAPON_INFO (sub_name,special_name,special_points,"
                f"level,weapon_class,zh_name,zh_sub_name,zh_special_name,name) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"
            )
        else:
            sql = (
                f"UPDATE WEAPON_INFO set sub_name=?,special_name=?,"
                f"special_points=?,level=?,weapon_class=?,zh_name=?,zh_sub_name=?,"
                f"zh_special_name=? where name=?"
            )
        c.execute(
            sql,
            (
                weapon.sub_name,
                weapon.special_name,
                weapon.special_points,
                weapon.level,
                weapon.weapon_class,
                weapon.zh_name,
                weapon.zh_sub_name,
                weapon.zh_special_name,
                weapon.name,
            ),
        )
        self.conn.commit()

    # 取武器数据
    def get_weapon_info(self, weapon_name) -> WeaponData:
        sql = (
            f"select name,sub_name,special_name,special_points,level,weapon_class,"
            f"zh_name,zh_sub_name,zh_special_name from WEAPON_INFO where name=?"
        )
        c = self.conn.cursor()
        c.execute(sql, (weapon_name,))
        row = c.fetchone()
        weapon = WeaponData(
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
        )
        self.conn.commit()
        return weapon

    # 新增或更新 武器图片数据
    # type_name = (main|sub|special|class)
    def add_or_modify_weapon_images(self, name, type_name, image):
        sql = f"select * from WEAPON_IMAGES where name=?"
        c = self.conn.cursor()
        c.execute(sql, (name,))
        data = c.fetchone()
        if not data:  # create user
            sql = f"INSERT INTO WEAPON_IMAGES (image, name, type) VALUES (?, ?, ?);"
        else:
            # 需要使用两个条件进行判定，因为有重名图片
            sql = f"UPDATE WEAPON_IMAGES set image=? where name=? AND type=?"
        c.execute(sql, (image, name, type_name))
        self.conn.commit()

    # 取武器图片数据
    def get_weapon_image(self, name, type_name) -> []:
        sql = f"select image from WEAPON_IMAGES where name=? AND type=?"
        c = self.conn.cursor()
        # 需要使用两个条件进行判定，因为有重名图片
        c.execute(sql, (name, type_name))
        data = c.fetchone()
        self.conn.commit()
        return data[0]
