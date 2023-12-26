#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import datetime
import json
import os

import httpx
from httpx import Response
from loguru import logger
from sqlalchemy import Column, String, create_engine, Integer, Boolean, Text, DateTime, func, Float
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

dir_plugin = os.path.abspath(os.path.join(__file__, os.pardir))
database_uri = f'sqlite:///{dir_plugin}/resource/data.sqlite'
database_uri_2 = f'sqlite:///{dir_plugin}/resource/data_friend.sqlite'

DIR_TEMP_IMAGE = f'{os.path.abspath(os.path.join(__file__, os.pardir))}/resource/temp_image'

Base = declarative_base()
Base_2 = declarative_base()


async def async_http_get(url: str) -> Response:
    """async http_get"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5.0)
        return response


async def get_file_url(url):
    """从网页读获取图片"""
    resp = await async_http_get(url)
    resp.read()
    data = resp.content
    return data


def init_path(path_folder):
    # 初始化文件夹路径
    if not os.path.exists(path_folder):
        os.mkdir(path_folder)


# Table
class UserTable(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_tg = Column(String(), unique=True, nullable=True)
    user_id_qq = Column(String(), unique=True, nullable=True)
    user_id_wx = Column(String(), unique=True, nullable=True)
    user_id_kk = Column(String(), unique=True, nullable=True)
    user_id_bind = Column(String(), unique=True, nullable=True)
    username = Column(String(), nullable=True)
    first_name = Column(String(), nullable=True)
    last_name = Column(String(), nullable=True)
    push = Column(Boolean(), default=False)
    push_cnt = Column(Integer(), default=0)
    cmd_cnt = Column(Integer(), default=0)
    map_cnt = Column(Integer(), default=0)
    api_key = Column(String(), nullable=True)
    api_notify = Column(Integer(), default=1)
    acc_loc = Column(String(), nullable=True)
    session_token = Column(String(), nullable=True)
    session_token_2 = Column(String(), nullable=True)
    gtoken = Column(String(), nullable=True)
    bullettoken = Column(String(), nullable=True)
    user_info = Column(Text(), nullable=True)
    cmd = Column(Text(), nullable=True)
    nickname = Column(String(), default='')
    friend_code = Column(String(), default='')
    user_id_sp = Column(String(), nullable=True)
    report_type = Column(Integer(), default=0)  # 1:daily, 2:weekly, 3:monthly, 4:season
    last_play_time = Column(DateTime(), nullable=True)
    first_play_time = Column(DateTime(), nullable=True)
    create_time = Column(DateTime(), default=func.now())
    update_time = Column(DateTime(), onupdate=func.now())


class GroupTable(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(), nullable=False)
    group_type = Column(String(), default='')
    group_name = Column(String(), default='')
    group_level = Column(String(), default='')
    member_count = Column(Integer(), default=0)
    cmd_cnt = Column(Integer(), default=0)
    map_cnt = Column(Integer(), default=0)
    cmd = Column(Text(), nullable=True)
    bot_map = Column(Integer(), default=1)
    bot_broadcast = Column(Integer(), default=1)
    group_memo = Column(String(), default='')
    max_member_count = Column(Integer(), default=0)
    member_id_list = Column(Text(), default='')
    group_create_time = Column(DateTime())
    create_time = Column(DateTime(), default=func.now())
    update_time = Column(DateTime(), onupdate=func.now())


class TopPlayer(Base):
    __tablename__ = 'top_player'

    id = Column(Integer, primary_key=True, autoincrement=True)
    top_id = Column(String(), default='')
    top_type = Column(String(), default='')
    rank = Column(Integer(), default=0)
    power = Column(String(), default='')
    player_name = Column(String(), default='')
    player_name_id = Column(String(), default='')
    player_code = Column(String(), default='')
    byname = Column(String(), default='')
    weapon_id = Column(Integer(), default=0)
    weapon = Column(String(), default='')
    play_time = Column(DateTime())
    create_time = Column(DateTime(), default=func.now())
    update_time = Column(DateTime(), onupdate=func.now())


class TopAll(Base):
    __tablename__ = 'top_all'

    id = Column(Integer, primary_key=True, autoincrement=True)
    top_id = Column(String(), default='')
    top_type = Column(String(), default='')
    rank = Column(Integer(), default=0)
    power = Column(String(), default='')
    player_name = Column(String(), default='')
    player_name_id = Column(String(), default='')
    player_code = Column(String(), default='', index=True)
    byname = Column(String(), default='')
    weapon_id = Column(Integer(), default=0)
    weapon = Column(String(), default='')
    play_time = Column(DateTime())
    create_time = Column(DateTime(), default=func.now())
    update_time = Column(DateTime(), onupdate=func.now())


class Weapon(Base):
    __tablename__ = 'weapon'

    id = Column(Integer, primary_key=True, autoincrement=True)
    weapon_id = Column(String(), default='')
    weapon_name = Column(String(), default='')
    image2d = Column(String(), default='')
    image2d_thumb = Column(String(), default='')
    image3d = Column(String(), default='')
    image3d_thumb = Column(String(), default='')
    create_time = Column(DateTime(), default=func.now())
    update_time = Column(DateTime(), onupdate=func.now())


class Report(Base):
    __tablename__ = 'report'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(), nullable=False)
    user_id_sp = Column(String(), default='')
    nickname = Column(String(), default='')
    name_id = Column(String(), default='')
    byname = Column(String(), default='')
    rank = Column(Integer, default='')
    udemae = Column(String(), default='')
    udemae_max = Column(String(), default='')
    total_cnt = Column(Integer, default='')
    win_cnt = Column(Integer, default='')
    lose_cnt = Column(Integer, default='')
    win_rate = Column(Float, default=None)
    paint = Column(Integer, default='')
    badges = Column(Integer, default='')
    event_gold = Column(Integer, default='')
    event_silver = Column(Integer, default='')
    event_bronze = Column(Integer, default='')
    event_none = Column(Integer, default='')
    open_gold = Column(Integer, default='')
    open_silver = Column(Integer, default='')
    open_bronze = Column(Integer, default='')
    open_none = Column(Integer, default='')
    max_power = Column(Float, default=None)
    x_ar = Column(Float, default=None)
    x_lf = Column(Float, default=None)
    x_gl = Column(Float, default=None)
    x_cl = Column(Float, default=None)
    coop_cnt = Column(Integer, default='')
    coop_gold_egg = Column(Integer, default='')
    coop_egg = Column(Integer, default='')
    coop_boss_cnt = Column(Integer, default='')
    coop_rescue = Column(Integer, default='')
    coop_point = Column(Integer, default='')
    coop_gold = Column(Integer, default='')
    coop_silver = Column(Integer, default='')
    coop_bronze = Column(Integer, default='')
    last_play_time = Column(DateTime(), nullable=True)
    create_time = Column(DateTime(), default=func.now())


class CommentTable(Base):
    __tablename__ = 'comment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_type = Column(String(), nullable=False)
    user_id = Column(String(), nullable=False)
    user_name = Column(String(), default='')
    user_icon = Column(String(), default='')
    group_id = Column(String(), default='')
    group_name = Column(String(), default='')
    group_icon = Column(String(), default='')
    message = Column(Text(), default='')
    is_login = Column(Integer(), default=0)
    is_delete = Column(Integer(), default=0)
    create_time = Column(DateTime(), default=func.now())
    update_time = Column(DateTime(), onupdate=func.now())


class TempImageTable(Base):
    __tablename__ = 'temp_image'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(), default='')
    name = Column(String(), default='')
    link = Column(String(), default='')
    file_name = Column(String(), default='')
    create_time = Column(DateTime(), default=func.now())
    update_time = Column(DateTime(), onupdate=func.now())


def GetInsertOrUpdateObj(cls, strFilter, **kw):
    """
    cls:            Model 类名
    strFilter:      filter的参数.eg:"name='name-14'"
    **kw:           【属性、值】字典,用于构建新实例，或修改存在的记录
    """
    session = DBSession()
    row = session.query(cls).filter(text(strFilter)).first()
    if not row:
        res = cls()
    else:
        res = row
    for k, v in kw.items():
        if hasattr(res, k):
            setattr(res, k, v)
    return res


async def model_get_or_set_temp_image(_type, name, link) -> TempImageTable:
    """获取或设置缓存图片"""
    session = DBSession()
    row: TempImageTable = session.query(TempImageTable).filter(
        (TempImageTable.type == _type) & (TempImageTable.name == name)).first()
    download_flag: bool = False
    temp_image = TempImageTable()
    if row:
        # 判断是否是用户图像缓存，并比对缓存数据是否需要更新
        if (row.type == "friend_icon" and row.link != link) or (row.type == "ns_friend_icon" and row.link != link):
            download_flag = True
        else:
            temp_image = copy.deepcopy(row)
    else:
        download_flag = True
    if download_flag:
        # 通过url下载图片储存至本地
        image_data = await get_file_url(link)
        file_name = ""
        if len(image_data) > 0:
            # 创建文件夹
            init_path(f"{DIR_TEMP_IMAGE}")
            init_path(f"{DIR_TEMP_IMAGE}/{_type}")

            file_name = f'{name}.png'
            with open(f"{DIR_TEMP_IMAGE}/{_type}/{file_name}", "wb") as f:
                f.write(image_data)
        temp_image = TempImageTable(
            type=_type,
            name=name,
            link=link,
            file_name=file_name
        )
        # 将复制值传给orm
        session.add(copy.deepcopy(temp_image))
    session.commit()
    session.close()
    return temp_image


async def get_temp_image_path(_type, name, link) -> str:
    """获取缓存文件路径"""
    row = await model_get_or_set_temp_image(_type, name, link)
    # logger.info(f"row为{row.__dict__}")
    file_name = row.file_name
    return f"{DIR_TEMP_IMAGE}/{_type}/{file_name}"


class UserFriendTable(Base_2):
    __tablename__ = 'user_friend'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(), nullable=False)
    friend_id = Column(String(), nullable=False)
    player_name = Column(String(), default='')
    nickname = Column(String(), default='')
    game_name = Column(String(), default='')
    user_icon = Column(String(), default='')
    create_time = Column(DateTime(), default=func.now())
    update_time = Column(DateTime(), onupdate=func.now())


engine = create_engine(database_uri)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)

engine_2 = create_engine(database_uri_2)
Base_2.metadata.create_all(engine_2)
DBSession_2 = sessionmaker(bind=engine_2)


def clean_db_cache():
    session = DBSession()
    session.execute(text("VACUUM"))
    session.commit()
    session.close()


def get_or_set_user(**kwargs):
    logger.debug(f'get_or_set_user: {kwargs}')
    try:
        user_id = kwargs.get('user_id')
        session = DBSession()

        if not user_id:
            logger.error('user_id is None')
            return

        user = session.query(UserTable).filter(
            (UserTable.id == user_id) | (UserTable.user_id_qq == user_id) | (UserTable.user_id_tg == user_id) |
            (UserTable.user_id_wx == user_id) | (UserTable.user_id_kk == user_id)
        ).first()
        if user:
            for k, v in kwargs.items():
                if getattr(user, k, '_empty') == '_empty' or k == 'user_id':
                    continue
                if getattr(user, k) == v:
                    continue
                logger.debug(f'update user {k}={v}')
                setattr(user, k, v)
                session.commit()
            user = session.query(UserTable).filter(
                (UserTable.id == user_id) | (UserTable.user_id_qq == user_id) |
                (UserTable.user_id_tg == user_id) | (UserTable.user_id_wx == user_id) |
                (UserTable.user_id_kk == user_id)).first()
            new_user = copy.deepcopy(user)
            session.commit()
            session.close()
            return new_user
        else:
            session.commit()
            session.close()
            logger.info('no user in db')

    except Exception as e:
        logger.error(f'get_or_set_user error: {e}')


def get_all_user():
    session = DBSession()
    users = session.query(UserTable).all()
    new_users = copy.deepcopy(users)
    session.commit()
    session.close()
    return new_users


def get_all_group():
    session = DBSession()
    users = session.query(GroupTable).all()
    new_users = copy.deepcopy(users)
    session.commit()
    session.close()
    return new_users


def set_db_info(**kwargs):
    logger.debug(f'set_db_info: {kwargs}')
    try:
        user_id = kwargs.get('user_id')
        group_id = kwargs.get('group_id')
        id_type = kwargs.get('id_type') or 'tg'

        if 'username' in kwargs:
            kwargs['username'] = kwargs['username'] or None

        raw_kwargs = kwargs.copy()

        session = DBSession()
        if user_id:
            query_lst = []
            if id_type == 'tg':
                query_lst.append(UserTable.user_id_tg == user_id)
            elif id_type == 'qq':
                query_lst.append(UserTable.user_id_qq == user_id)
            elif id_type == 'wx':
                query_lst.append(UserTable.user_id_wx == user_id)
            elif id_type == 'kk':
                query_lst.append(UserTable.user_id_kk == user_id)
            if query_lst:
                user = session.query(UserTable).filter(*query_lst).first()
                if user:
                    kwargs = raw_kwargs.copy()
                    if kwargs.get('cmd'):
                        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        str_cmd = f"{now} {kwargs.get('cmd')}"
                        if kwargs.get('group_name'):
                            str_cmd = f"{str_cmd} @{kwargs.get('group_name') or ''}({group_id or ''})"
                        if user.cmd:
                            new_cmd = user.cmd + '\n' + str_cmd
                        else:
                            new_cmd = str_cmd
                        kwargs['cmd'] = new_cmd
                        if kwargs.get('cmd_cnt'):
                            kwargs['cmd_cnt'] = user.cmd_cnt + 1
                        if kwargs.get('map_cnt'):
                            kwargs['map_cnt'] = user.map_cnt + 1
                    if kwargs.get('user_info'):
                        old_user_info = json.loads(user.user_info) if user.user_info else {}
                        new_user_info = json.loads(kwargs.get('user_info'))
                        new_user_info.update(old_user_info)
                        kwargs['user_info'] = json.dumps(new_user_info)

                    for k, v in kwargs.items():
                        if getattr(user, k, '_empty') == '_empty':
                            continue
                        if getattr(user, k) == v:
                            continue
                        logger.debug(f'update user {user.id}: {k}={v}')
                        setattr(user, k, v)
                        session.commit()
                else:
                    new_user = UserTable(
                        user_id_tg=user_id if id_type == 'tg' else None,
                        user_id_qq=user_id if id_type == 'qq' else None,
                        user_id_wx=user_id if id_type == 'wx' else None,
                        user_id_kk=user_id if id_type == 'kk' else None,
                        username=kwargs.get('username'),
                        first_name=kwargs.get('first_name'),
                        last_name=kwargs.get('last_name'),
                    )
                    session.add(new_user)
                    session.commit()

        if group_id:
            group = session.query(GroupTable).filter(GroupTable.group_id == group_id,
                                                     GroupTable.group_type == id_type).first()
            if group:
                kwargs = raw_kwargs.copy()
                if kwargs.get('cmd'):
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    str_cmd = f"{now} {kwargs.get('cmd')}"
                    str_cmd = f"{str_cmd} @{kwargs.get('username') or ''}({kwargs.get('user_id') or ''})"
                    if group.cmd:
                        new_cmd = group.cmd + '\n' + str_cmd
                    else:
                        new_cmd = str_cmd
                    kwargs['cmd'] = new_cmd
                    if kwargs.get('cmd_cnt'):
                        kwargs['cmd_cnt'] = group.cmd_cnt + 1
                    if kwargs.get('map_cnt'):
                        kwargs['map_cnt'] = group.map_cnt + 1

                for k, v in kwargs.items():
                    if getattr(group, k, '_empty') == '_empty':
                        continue
                    if getattr(group, k) == v:
                        continue
                    logger.debug(f'update group {k}={v}')
                    setattr(group, k, v)
                    session.commit()
            else:
                new_group = GroupTable(
                    group_id=group_id,
                    group_name=kwargs.get('group_name'),
                    group_type=id_type,
                )
                session.add(new_group)
                session.commit()

        session.close()
    except Exception as e:
        logger.error(f'set_db_info error: {e}')


def get_user(**kwargs):
    logger.debug(f'get_user: {kwargs}')
    try:
        user_id = kwargs.get('user_id')
        session = DBSession()

        user = session.query(UserTable).filter(
            (UserTable.id == user_id) | (UserTable.user_id_qq == user_id) | (UserTable.user_id_tg == user_id) |
            (UserTable.user_id_wx == user_id) | (UserTable.user_id_kk == user_id)
        ).first()
        if user:
            logger.debug(f'get user from db: {user.id}, {user.username}, {kwargs}')
            new_user = copy.deepcopy(user)
            session.commit()
            session.close()
            return new_user
        else:
            session.commit()
            session.close()
            return UserTable()

    except Exception as e:
        logger.error(f'get_user error: {e}')


def write_top_player(row):
    top_id, _top_type, rank, power, name, name_id, player_code, byname, weapon_id, weapon = row

    session = DBSession()
    _dict = {
        'top_id': top_id,
        'top_type': _top_type,
        'rank': rank,
        'power': power,
        'player_name': name,
        'player_name_id': name_id,
        'player_code': player_code,
        'byname': byname,
        'weapon_id': weapon_id,
        'weapon': weapon,
    }
    new_user = TopPlayer(**_dict)
    session.add(new_user)
    session.commit()
    session.close()


def clean_top_player(top_id):
    session = DBSession()
    session.query(TopPlayer).filter(TopPlayer.top_id == top_id).delete()
    session.commit()
    session.close()


def get_top_player(player_code):
    session = DBSession()
    user = session.query(func.min(TopPlayer.rank), func.max(TopPlayer.power)
                         ).filter(TopPlayer.player_code == player_code).first()
    new_user = copy.deepcopy(user)
    session.commit()
    session.close()
    return new_user


def get_top_player_row(player_code):
    session = DBSession()
    user = session.query(TopPlayer).filter(
        TopPlayer.player_code == player_code).order_by(TopPlayer.power.desc()).first()
    new_user = copy.deepcopy(user)
    session.commit()
    session.close()
    return new_user


def model_add_report(**kwargs):
    logger.debug(f'model_add_report: {kwargs}')
    _dict = kwargs
    user_id_sp = _dict.get('user_id_sp')
    if not user_id_sp:
        logger.warning(f'no user_id_sp: {_dict}')
        return
    session = DBSession()
    _res = session.query(Report).filter(Report.user_id_sp == user_id_sp).order_by(Report.create_time.desc()).first()
    if _res and _res.create_time.date() >= datetime.datetime.utcnow().date():
        logger.debug(f'already saved report: {_dict.get("user_id")}, {user_id_sp}, {_dict.get("nickname")}')
        session.close()
        return

    new_report = Report(**_dict)
    session.add(new_report)
    session.commit()
    session.close()


def model_get_report(**kwargs):
    user_id_sp = kwargs.get('user_id_sp')
    if not user_id_sp:
        return None
    session = DBSession()

    #     query = [Report.user_id_sp == user_id_sp]
    #     report = session.query(Report).filter(*query).order_by(Report.create_time.desc()).all()

    report = session.query(Report).from_statement(text("""
        SELECT *
        FROM report WHERE (user_id_sp, last_play_time, create_time) IN
        ( SELECT user_id_sp, last_play_time, MAX(create_time)
          FROM report
          GROUP BY user_id_sp, last_play_time)
        and user_id_sp=:user_id_sp
        order by create_time desc""")
                                                  ).params(user_id_sp=user_id_sp).all()

    new_report = copy.deepcopy(report)
    session.commit()
    session.close()
    return new_report


def model_get_map_group_id_list():
    session = DBSession()
    query = [GroupTable.group_id != '', GroupTable.bot_map == 0]
    group_id_list = session.query(GroupTable.group_id).filter(*query).all()
    session.close()
    id_lst = [i[0] for i in group_id_list]
    session.commit()
    session.close()
    return id_lst


def model_get_login_user(player_code):
    session = DBSession()
    user = session.query(UserTable).filter(UserTable.user_id_sp == player_code).first()
    new_user = copy.deepcopy(user)
    session.commit()
    session.close()
    return new_user


def model_get_user_friend(nickname) -> UserFriendTable:
    session = DBSession_2()
    user = session.query(UserFriendTable).filter(
        UserFriendTable.game_name == nickname
    ).order_by(UserFriendTable.create_time.desc()).first()
    new_user = copy.deepcopy(user)
    session.commit()
    session.close()
    return new_user


def model_set_user_friend(data_lst):
    report_logger = logger.bind(report=True)
    session = DBSession_2()
    for r in data_lst:
        user = session.query(UserFriendTable).filter(UserFriendTable.friend_id == r[1]).first()
        game_name = r[2] or r[3]
        if user:
            is_change = False
            if r[2] and user.game_name != game_name:
                is_change = True
            if is_change is False and user.user_icon != r[4]:
                is_change = True

            if is_change:
                report_logger.debug(f'change {user.id:>5}, {user.player_name}, {user.nickname}, {user.game_name}')
                report_logger.debug(f'cha--> {user.id:>5}, {r[2]}, {r[3]}, {game_name}')
                user.player_name = r[2]
                user.nickname = r[3]
                user.user_icon = r[4]
                user.game_name = game_name
                session.commit()
                report_logger.debug(f'edit user_friend: {user.id:>5}, {r[1]}, {r[2]}, {r[3]}, {game_name}')

        else:
            _dict = {
                'user_id': '',
                'friend_id': r[1],
                'player_name': r[2],
                'nickname': r[3],
                'game_name': game_name,
                'user_icon': r[4],
            }
            new_user = UserFriendTable(**_dict)
            session.add(new_user)
            session.commit()
            report_logger.debug(f'add user_friend: {r[1]}, {r[2]}, {r[3]}, {game_name}')

    session.close()


def model_add_comment(**kwargs):
    logger.debug(f'model_add_report: {kwargs}')
    _dict = {
        'bot_type': kwargs.get('bot_type') or 'qq',
        'user_id': kwargs.get('user_id'),
        'user_name': kwargs.get('user_name'),
        'user_icon': kwargs.get('user_icon'),
        'group_id': kwargs.get('group_id'),
        'group_name': kwargs.get('group_name'),
        'group_icon': kwargs.get('group_icon'),
        'message': kwargs.get('message'),
        'create_time': datetime.datetime.now(),
    }
    session = DBSession()
    new_report = CommentTable(**_dict)
    session.add(new_report)
    session.commit()
    session.close()


def model_get_comment():
    session = DBSession()
    query = [CommentTable.is_delete != 1]
    comment = session.query(CommentTable).filter(*query).order_by(CommentTable.create_time).all()
    new_comment = copy.deepcopy(comment)
    session.commit()
    session.close()
    return new_comment


def write_top_all(row):
    top_id, _top_type, rank, power, name, name_id, player_code, byname, weapon_id, weapon, play_time = row

    session = DBSession()
    _dict = {
        'top_id': top_id,
        'top_type': _top_type,
        'rank': rank,
        'power': power,
        'player_name': name,
        'player_name_id': name_id,
        'player_code': player_code,
        'byname': byname,
        'weapon_id': weapon_id,
        'weapon': weapon,
        'play_time': play_time
    }
    new_user = TopAll(**_dict)
    session.add(new_user)
    session.commit()
    session.close()


def clean_top_all(top_id):
    session = DBSession()
    session.query(TopAll).filter(TopAll.top_id == top_id).delete()
    session.commit()
    session.close()


def get_top_all(player_code):
    session = DBSession()
    user = session.query(TopAll).filter(TopAll.player_code == player_code).all()
    new_user = copy.deepcopy(user)
    session.commit()
    session.close()
    return new_user


def get_top_all_row(player_code) -> TopAll:
    session = DBSession()
    user = session.query(TopAll).filter(
        TopAll.player_code == player_code).order_by(TopAll.power.desc()).first()
    new_user = copy.deepcopy(user)
    session.commit()
    session.close()
    return new_user


def get_top_all_by_top_type(top_type):
    session = DBSession()
    top = session.query(TopAll).where(TopAll.top_type.contains(top_type)).all()
    new_top = copy.deepcopy(top)
    session.commit()
    session.close()
    return new_top


def get_weapon() -> Weapon:
    session = DBSession()
    weapon = session.query(Weapon).all()
    _dict = dict((str(i.weapon_id), dict(name=i.weapon_name, url=i.image2d_thumb)) for i in weapon)
    session.commit()
    session.close()
    return _dict
