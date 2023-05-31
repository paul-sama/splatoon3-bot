import base64
import json

from collections import defaultdict
from datetime import datetime as dt
from nonebot import logger
from nonebot.adapters import Event, Bot
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.onebot.v11 import Bot as QQBot

from .db_sqlite import get_user, get_or_set_user
from .splat import Splatoon
from .sp3msg import get_battle_msg, get_coop_msg, get_summary, get_statics, get_friends, get_ns_friends
from .sp3msg_md import get_battle_msg as get_battle_msg_md, get_coop_msg as get_coop_msg_md
from .utils import bot_send, INTERVAL


def get_user_db_info(user_id):
    user = get_user(user_id=user_id)

    msg = f"""
```
user_name: {user.username}
gtoken: {user.gtoken}
bullettoken: {user.bullettoken}
session_token: {user.session_token}
push: {user.push}
push_cnt: {user.push_cnt}
api_key: {user.api_key}
acc_loc: {user.acc_loc}
user_info: {user.user_info}
```
/clear\_db\_info  clear your data
"""
    return msg


def get_last_msg(splt, _id, extra_info, is_battle=True, **kwargs):
    try:
        if is_battle:
            battle_detail = splt.get_battle_detail(_id)
            kwargs['splt'] = splt
            if kwargs.get('get_pic'):
                msg = get_battle_msg_md(extra_info, battle_detail, **kwargs)
            else:
                msg = get_battle_msg(extra_info, battle_detail, **kwargs)
        else:
            coo_detail = splt.get_coop_detail(_id)
            if kwargs.get('get_pic'):
                msg = get_coop_msg_md(extra_info, coo_detail)
            else:
                msg = get_coop_msg(extra_info, coo_detail)
    except Exception as e:
        logger.exception(e)
        msg = f'get last {"battle" if is_battle else "coop"} failed, please try again later.'
    return msg


async def get_last_battle_or_coop(user_id, for_push=False, get_battle=False, get_coop=False, get_pic=False, idx=0):
    user = get_user(user_id=user_id)
    splt = Splatoon(user.id, user.session_token)

    # get last battle
    res = splt.get_recent_battles(skip_check_token=True if for_push else False)
    if not res:
        return f'`network error, please try again later.`'

    b_info = res['data']['latestBattleHistories']['historyGroups']['nodes'][0]['historyDetails']['nodes'][idx]
    battle_id = b_info['id']
    battle_t = base64.b64decode(battle_id).decode('utf-8').split('_')[0].split(':')[-1]

    # get last coop
    if (dt.utcnow() - dt.strptime(battle_t, '%Y%m%dT%H%M%S')).seconds < 60:
        # played battle in 1 minute, no need to get coop
        res = None
    else:
        res = splt.get_coops()
    try:
        coop_info = {
            'coop_point': res['data']['coopResult']['pointCard']['regularPoint'],
            'coop_eggs': res['data']['coopResult']['historyGroups']['nodes'][0]['highestResult'].get('jobScore') or 0
        }
        coop_id = res['data']['coopResult']['historyGroups']['nodes'][0]['historyDetails']['nodes'][idx]['id']
        coop_t = base64.b64decode(coop_id).decode('utf-8').split('_')[0].split(':')[-1]
    except:
        coop_info = {}
        coop_id = ''
        coop_t = ''

    if get_coop:
        get_battle = False
        battle_t = ''

    if get_battle or battle_t > coop_t:
        if for_push:
            return battle_id, b_info, True

        try:
            user_info = json.loads(user.user_info)
        except:
            user_info = {}
        msg = get_last_msg(splt, battle_id, b_info, battle_show_type=user_info.get('battle_show_type'), get_pic=get_pic)
        return msg
    else:
        if for_push:
            return coop_id, coop_info, False
        msg = get_last_msg(splt, coop_id, coop_info, False, get_pic=get_pic)
        return msg


def get_me(user_id):
    user = get_user(user_id=user_id)
    splt = Splatoon(user.id, user.session_token)
    res = splt.get_summary()
    all_res = splt.get_all_res()
    coop = splt.get_coop_summary()
    try:
        msg = get_summary(res, all_res, coop, lang=user.acc_loc)
    except Exception as e:
        logger.exception(e)
        msg = f'get summary failed, please try again later.'
    logger.debug(msg)
    return msg


async def push_latest_battle(bot: Bot, event: Event, job_data: dict):
    job_id = job_data.get('job_id')
    logger.debug(f'push_latest_battle {job_id}, {job_data}')

    user_id = job_data.get('user_id')

    user = get_user(user_id=user_id)
    if not user or user.push is False:
        logger.info(f'stop by user clear db: {job_id} stop')
        from splatoon3_bot.plugins.splatoon3_bot import scheduler
        scheduler.remove_job(job_id)
        return

    push_cnt = user.push_cnt + 1
    user = get_or_set_user(user_id=user.id, push_cnt=push_cnt)
    if push_cnt % 60 == 0:
        # show log every 10 minutes
        logger.info(f'push_latest_battle: {user.username}, {job_id}')

    data = job_data or {}
    res = await get_last_battle_or_coop(user_id, for_push=True)
    if not res:
        logger.debug('no new battle or coop')
        return
    battle_id, _info, is_battle = res

    db_user_info = defaultdict(str)
    if user.user_info:
        db_user_info = json.loads(user.user_info)
        last_battle_id = db_user_info.get('battle_id')
        # logger.info(f'last_battle_id: {last_battle_id}')
        if last_battle_id == battle_id:
            if push_cnt * INTERVAL / 60 > 30:
                from splatoon3_bot.plugins.splatoon3_bot import scheduler
                scheduler.remove_job(job_id)
                get_or_set_user(user_id=user_id, push=False)
                msg = 'No game record for 30 minutes, stop push.'
                if isinstance(bot, QQBot):
                    msg = '30分钟内没有游戏记录，停止推送。'

                if data.get('current_statics'):
                    msg += get_statics(data['current_statics'])
                logger.info(f'{user.username}, {msg}')
                await bot_send(bot, event, message=msg)
                return
            return

    logger.info(f'{user.id}, {user.username} get new {"battle" if is_battle else "coop"}!')
    db_user_info['battle_id'] = battle_id
    get_or_set_user(user_id=user.id, user_info=json.dumps(db_user_info), push_cnt=0)
    splt = Splatoon(user_id, user.session_token)
    msg = get_last_msg(splt, battle_id, _info, is_battle, battle_show_type=db_user_info.get('battle_show_type'), **data)

    r = await bot_send(bot, event, message=msg, parse_mode='Markdown')
    if job_data.get('group_id') and r:
        message_id = ''
        if isinstance(bot, QQBot):
            message_id = r.get('message_id')
            if data.get('last_group_msg_id'):
                await bot.call_api('delete_msg', message_id=data['last_group_msg_id'])
        elif isinstance(bot, TGBot):
            message_id = r.message_id
            # qq 五分钟后消息撤回失效
            # if data.get('last_group_msg_id'):
            #    await bot.call_api('delete_message', message_id=data['last_group_msg_id'], chat_id=r.chat.id)
        data['last_group_msg_id'] = message_id


def get_friends_msg(user_id):
    user = get_or_set_user(user_id=user_id)
    splt = Splatoon(user_id, user.session_token)
    msg = get_friends(splt, lang=user.acc_loc)
    logger.debug(msg)
    return msg


def get_ns_friends_msg(user_id):
    user = get_or_set_user(user_id=user_id)
    splt = Splatoon(user_id, user.session_token)
    msg = get_ns_friends(splt)
    logger.debug(msg)
    return msg
