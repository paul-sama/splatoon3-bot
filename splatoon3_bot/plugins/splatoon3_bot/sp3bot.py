import base64
import json

from collections import defaultdict
from datetime import datetime as dt
from nonebot import logger
from nonebot.adapters import Event, Bot
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.onebot.v11 import Bot as QQBot

from .db_sqlite import get_user, get_or_set_user, get_all_user
from .splat import Splatoon, API_URL
from .sp3msg import (
    get_battle_msg, get_coop_msg, get_summary, get_statics, get_friends, get_ns_friends, get_x_top, get_my_schedule
)
from .sp3msg_md import (
    get_battle_msg as get_battle_msg_md, get_coop_msg as get_coop_msg_md, get_history, get_friends as get_friends_md,
    get_ns_friends, get_top_md
)
from .splatnet_image import get_app_screenshot
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


async def get_last_msg(splt, _id, extra_info, is_battle=True, **kwargs):
    try:
        if is_battle:
            battle_detail = await splt.get_battle_detail(_id)

            if kwargs.get('get_player_code'):
                _idx = kwargs.get('get_player_code', 1) - 1
                battle_detail = battle_detail['data']['vsHistoryDetail'] or {}
                teams = [battle_detail['myTeam']] + battle_detail['otherTeams']
                p_lst = []
                for t in teams:
                    for p in t['players']:
                        p_lst.append(p)
                player_code = (base64.b64decode(p_lst[_idx]['id']).decode('utf-8') or '').split(':u-')[-1]
                return player_code

            kwargs['splt'] = splt
            if kwargs.get('get_pic') or kwargs.get('get_image'):
                msg = await get_battle_msg_md(extra_info, battle_detail, **kwargs)
            else:
                msg = await get_battle_msg(extra_info, battle_detail, **kwargs)
        else:
            coo_detail = await splt.get_coop_detail(_id)
            if kwargs.get('get_pic') or kwargs.get('get_image'):
                msg = get_coop_msg_md(extra_info, coo_detail, **kwargs)
            else:
                msg = get_coop_msg(extra_info, coo_detail)
    except Exception as e:
        logger.exception(e)
        msg = f'get last {"battle" if is_battle else "coop"} failed, please try again later.'
    return msg


async def get_last_battle_or_coop(user_id, for_push=False, get_battle=False, get_coop=False, get_pic=False, idx=0,
                                  get_screenshot=False, get_image=False, mask=False, get_player_code=False):
    user = get_user(user_id=user_id)
    splt = Splatoon(user.id, user.session_token)

    # get last battle
    res = await splt.get_recent_battles(skip_check_token=True if for_push else False)
    if not res:
        # token 每两小时更新，再次尝试一次
        res = await splt.get_recent_battles()
        if not res:
            return f'`网络错误，请稍后再试.`'

    b_info = res['data']['latestBattleHistories']['historyGroups']['nodes'][0]['historyDetails']['nodes'][idx]
    battle_id = b_info['id']
    battle_t = base64.b64decode(battle_id).decode('utf-8').split('_')[0].split(':')[-1]

    # get last coop
    res = await splt.get_coops()
    try:
        # token 每两小时更新，再次尝试一次
        if not res: res = await splt.get_coops()
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
        if get_screenshot:
            try:
                user = get_user(user_id=user_id)
                url = f"{API_URL}/history/detail/{battle_id}?lang=zh-CN"
                pic = await get_app_screenshot(user.gtoken, url=url, mask=mask)
            except Exception as e:
                logger.exception(e)
                pic = None
            return pic

        try:
            user_info = json.loads(user.user_info)
        except:
            user_info = {}
        msg = await get_last_msg(splt, battle_id, b_info, battle_show_type=user_info.get('battle_show_type'),
                                 get_pic=get_pic, get_image=get_image, mask=mask, get_player_code=get_player_code)
        return msg
    else:
        if for_push:
            return coop_id, coop_info, False
        if get_screenshot:
            try:
                user = get_user(user_id=user_id)
                url = f"{API_URL}/coop/{coop_id}?lang=zh-CN"
                pic = await get_app_screenshot(user.gtoken, url=url, mask=mask)
            except Exception as e:
                logger.exception(e)
                pic = None
            return pic

        msg = await get_last_msg(splt, coop_id, coop_info, False, get_pic=get_pic, get_image=get_image, mask=mask)
        return msg


async def get_me(user_id):
    user = get_user(user_id=user_id)
    splt = Splatoon(user.id, user.session_token)
    res = await splt.get_summary()
    all_res = await splt.get_all_res()
    coop = await splt.get_coop_summary()
    try:
        msg = get_summary(res, all_res, coop, lang=user.acc_loc)
    except Exception as e:
        logger.exception(e)
        msg = f'获取数据失败，请稍后再试或重新登录 /login'
    logger.debug(msg)
    return msg


async def push_latest_battle(bot: Bot, event: Event, job_data: dict):
    job_id = job_data.get('job_id')
    logger.debug(f'push_latest_battle {job_id}, {job_data}')

    user_id = job_data.get('user_id')
    push_cnt = job_data.get('push_cnt', 0)

    user = get_user(user_id=user_id)
    if not user or user.push is False:
        logger.info(f'stop by user clear db: {job_id} stop')
        from splatoon3_bot.plugins.splatoon3_bot import scheduler
        scheduler.remove_job(job_id)
        return

    push_cnt += 1
    job_data['push_cnt'] = push_cnt
    if push_cnt % 60 == 0:
        # show log every 10 minutes
        logger.info(f'push_latest_battle: {user.username}, {job_id}')

    data = job_data or {}

    # QQ 群聊2分钟内撤回
    if isinstance(bot, QQBot) and push_cnt == 10 and job_data.get('group_id'):
        if data.get('last_group_msg_id'):
            try:
                await bot.call_api('delete_msg', message_id=data['last_group_msg_id'])
            except Exception as e:
                logger.warning(f'push_latest_battle delete_msg failed\n{e}')

    get_image = data.get('get_image', False)
    try:
        res = await get_last_battle_or_coop(user_id, for_push=True, get_image=get_image)
        battle_id, _info, is_battle = res
    except Exception as e:
        logger.debug(f'no new battle or coop, {e}')
        return

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

                if data.get('current_statics') and data['current_statics'].get('TOTAL'):
                    msg += get_statics(data['current_statics'])
                logger.info(f'{user.username}, {msg}')
                await bot_send(bot, event, message=msg, parse_mode='Markdown', skip_log_cmd=True)
                return
            return

    logger.info(f'{user.id}, {user.username} get new {"battle" if is_battle else "coop"}!')
    db_user_info['battle_id'] = battle_id
    get_or_set_user(user_id=user.id, user_info=json.dumps(db_user_info))
    job_data['push_cnt'] = 0
    splt = Splatoon(user_id, user.session_token)
    msg = await get_last_msg(splt, battle_id, _info, is_battle, battle_show_type=db_user_info.get('battle_show_type'), **data)

    image_width = 630 if get_image else 1000
    r = await bot_send(bot, event, message=msg, parse_mode='Markdown',
                       reply_to_message_id=None, image_width=image_width, skip_log_cmd=True)
    if job_data.get('group_id') and r:
        message_id = ''
        if isinstance(bot, QQBot):
            message_id = r.get('message_id')
            # qq 五分钟后消息撤回失效
            # if data.get('last_group_msg_id'):
            #     await bot.call_api('delete_msg', message_id=data['last_group_msg_id'])
        elif isinstance(bot, TGBot):
            message_id = r.message_id
            if data.get('last_group_msg_id'):
               await bot.call_api('delete_message', message_id=data['last_group_msg_id'], chat_id=r.chat.id)
        data['last_group_msg_id'] = message_id


async def get_friends_msg(user_id, text=False):
    user = get_or_set_user(user_id=user_id)
    splt = Splatoon(user_id, user.session_token)
    if text:
        msg = await get_friends(splt, lang=user.acc_loc)
    else:
        msg = await get_friends_md(splt, lang=user.acc_loc)
    logger.debug(msg)
    return msg


def get_ns_friends_msg(user_id):
    user = get_or_set_user(user_id=user_id)
    splt = Splatoon(user_id, user.session_token)
    msg = get_ns_friends(splt)
    logger.debug(msg)
    return msg


async def get_x_top_msg():
    users = get_all_user()
    splt = None
    for u in users:
        if u and u.session_token:
            user_id = u.user_id_qq or u.user_id_tg or u.id
            splt = Splatoon(user_id, u.session_token)
            break
    msg = await get_x_top(splt)
    logger.debug(msg)
    return msg


async def get_my_schedule_msg(user_id):
    user = get_or_set_user(user_id=user_id)
    splt = Splatoon(user_id, user.session_token)
    msg = await get_my_schedule(splt)
    # logger.debug(msg)
    return msg


async def get_screenshot_image(user_id, key=None):

    user = get_or_set_user(user_id=user_id)
    splt = Splatoon(user_id, user.session_token)
    await splt.test_page()
    user = get_or_set_user(user_id=user_id)
    try:
        img = await get_app_screenshot(user.gtoken, key)
    except Exception as e:
        logger.exception(e)
        img = None
    return img


async def get_history_msg(user_id, _type='open'):
    user = get_or_set_user(user_id=user_id)
    splt = Splatoon(user_id, user.session_token)
    msg = await get_history(splt, _type=_type)
    logger.debug(msg)
    return msg


def get_friend_code(user_id):
    user = get_or_set_user(user_id=user_id)
    if user and user.friend_code:
        return f'{user.nickname}: {user.friend_code}'

    splt = Splatoon(user_id, user.session_token)
    res = splt.app_ns_myself() or {}
    logger.debug(res)

    msg = '.'
    code = res.get('code')
    if code:
        get_or_set_user(user_id=user_id, friend_code=code)
        msg = f'{res.get("name")}: {code}'
    return msg


async def get_top(user_id, battle=None, player=None):
    logger.info(f'get_top: {user_id}, {battle}, {player}')
    if not battle:
        user = get_user(user_id=user_id)
        player_code = user.user_id_sp
    else:
        player_code = await get_last_battle_or_coop(user_id, get_battle=True, idx=battle - 1, get_player_code=player)

    photo = get_top_md(player_code)
    return photo
