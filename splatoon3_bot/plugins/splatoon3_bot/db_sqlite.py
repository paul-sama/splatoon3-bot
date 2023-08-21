#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import os
from loguru import logger
from sqlalchemy import Column, String, create_engine, Integer, Boolean, Text, DateTime, func, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

dir_plugin = os.path.abspath(os.path.join(__file__, os.pardir))
database_uri = f'sqlite:///{dir_plugin}/resource/data.sqlite'

Base = declarative_base()


# Table
class UserTable(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_tg = Column(String(), unique=True, nullable=True)
    user_id_qq = Column(String(), unique=True, nullable=True)
    username = Column(String(), nullable=True)
    first_name = Column(String(), nullable=True)
    last_name = Column(String(), nullable=True)
    push = Column(Boolean(), default=False)
    push_cnt = Column(Integer(), default=0)
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
    group_name = Column(String(), default='')
    group_type = Column(String(), default='')
    cmd = Column(Text(), nullable=True)
    bot_map = Column(Integer(), default=1)
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


class UserFriendTable(Base):
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


engine = create_engine(database_uri, connect_args={"check_same_thread": False})

Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)


def get_or_set_user(**kwargs):
    logger.debug(f'get_or_set_user: {kwargs}')
    try:
        user_id = kwargs.get('user_id')
        session = DBSession()

        if not user_id:
            logger.error('user_id is None')
            return

        user = session.query(UserTable).filter(
            (UserTable.id == user_id) | (UserTable.user_id_qq == user_id) | (UserTable.user_id_tg == user_id)).first()
        if user:
            for k, v in kwargs.items():
                if getattr(user, k, '_empty') == '_empty' or k == 'user_id':
                    continue
                if getattr(user, k) == v:
                    continue
                logger.debug(f'update user {k}={v}')
                setattr(user, k, v)
                session.commit()
            user = session.query(UserTable).filter((UserTable.id == user_id) | (UserTable.user_id_qq == user_id) |
                                                   (UserTable.user_id_tg == user_id)).first()
            session.close()
            return user
        else:
            logger.info('no user in db')

    except Exception as e:
        logger.error(f'get_or_set_user error: {e}')


def get_all_user():
    session = DBSession()
    users = session.query(UserTable).all()
    session.close()
    return users


def set_db_info(**kwargs):
    logger.debug(f'set_db_info: {kwargs}')
    try:
        user_id = kwargs.get('user_id')
        group_id = kwargs.get('group_id')
        id_type = kwargs.get('id_type') or 'tg'

        if group_id and kwargs.get('cmd'):
            _cmd = kwargs.get('cmd')
            if not isinstance(_cmd, str) or (
                    _cmd[1:4].strip() not in [
                'log', 'las', 'ss', 'scr', 'me', 'hel', 'sta', 'x_t', 'my_', 'coo', 'fri', 'ns_', 'rep', 'sp', 'ns', 'fr',
                '文档', '帮助', '图', '图图', '图图图', '工', '全部工', '全部开', '全部挑']
            ):
                del kwargs['cmd']

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

                    for k, v in kwargs.items():
                        if getattr(user, k, '_empty') == '_empty':
                            continue
                        if getattr(user, k) == v:
                            continue
                        logger.debug(f'update user {k}={v}')
                        setattr(user, k, v)
                        session.commit()
                else:
                    new_user = UserTable(
                        user_id_tg=user_id if id_type == 'tg' else None,
                        user_id_qq=user_id if id_type == 'qq' else None,
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
            (UserTable.id == user_id) | (UserTable.user_id_qq == user_id) | (UserTable.user_id_tg == user_id)).first()
        if user:
            logger.debug(f'get user from db: {user.id}, {user.username}, {kwargs}')
            session.close()
            return user

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
    session.close()
    return user


def model_add_report(**kwargs):
    logger.debug(f'model_add_report: {kwargs}')
    _dict = kwargs
    session = DBSession()
    new_report = Report(**_dict)
    session.add(new_report)
    session.commit()
    session.close()


def model_get_report(**kwargs):
    user_id = kwargs.get('user_id')
    if not user_id:
        return None
    session = DBSession()
    query = [Report.user_id == user_id]
    report = session.query(Report).filter(*query).order_by(Report.create_time.desc()).all()
    session.close()
    return report


def model_get_map_group_id_list():
    session = DBSession()
    query = [GroupTable.group_id != '', GroupTable.bot_map == 0]
    group_id_list = session.query(GroupTable.group_id).filter(*query).all()
    session.close()
    id_lst = [i[0] for i in group_id_list]
    return id_lst


def model_get_login_user(player_code):
    session = DBSession()
    user = session.query(UserTable).filter(UserTable.user_id_sp == player_code).first()
    session.close()
    return user


def model_get_user_friend(nickname):
    session = DBSession()
    user = session.query(UserFriendTable).filter(
        UserFriendTable.game_name == nickname
    ).order_by(UserFriendTable.create_time.desc()).first()
    session.close()
    return user


def model_set_user_friend(data_lst):
    session = DBSession()
    for r in data_lst:
        user = session.query(UserFriendTable).filter(UserFriendTable.friend_id == r[1]).first()
        game_name = r[2] or r[3]
        if user:
            user.player_name = r[2]
            user.nickname = r[3]
            user.game_name = game_name
            user.user_icon = r[4]
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
    session.close()
    return comment
