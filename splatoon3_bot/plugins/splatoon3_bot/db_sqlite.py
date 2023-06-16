#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from loguru import logger
from sqlalchemy import Column, String, create_engine, Integer, Boolean, Text, DateTime, func
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
    username = Column(String(), unique=True, nullable=True)
    first_name = Column(String(), nullable=True)
    last_name = Column(String(), nullable=True)
    push = Column(Boolean(), default=False)
    push_cnt = Column(Integer(), default=0)
    api_key = Column(String(), nullable=True)
    acc_loc = Column(String(), nullable=True)
    session_token = Column(String(), nullable=True)
    session_token_2 = Column(String(), nullable=True)
    gtoken = Column(String(), nullable=True)
    bullettoken = Column(String(), nullable=True)
    user_info = Column(Text(), nullable=True)
    nickname = Column(String(), default='')
    friend_code = Column(String(), default='')
    user_id_sp = Column(String(), nullable=True)
    create_time = Column(DateTime(), default=func.now())
    update_time = Column(DateTime(), onupdate=func.now())


class GroupTable(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(), nullable=False)
    group_name = Column(String(), default='')
    group_type = Column(String(), default='')
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

        if 'username' in kwargs:
            kwargs['username'] = kwargs['username'] or None
            logger.debug(f'set_db_info: {kwargs}')

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
