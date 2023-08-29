
import json
from collections import defaultdict
from datetime import datetime as dt

from nonebot import on_command, logger, get_bots, permission
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Bot as QQBot, Message
from .utils import check_session_handler, bot_send
from .db_sqlite import get_user, get_or_set_user, get_all_group


@on_command("broadcast", block=True).handle()
@check_session_handler
async def _broadcast(bot: QQBot, event: Event):
    user_id = event.get_user_id()
    user = get_user(user_id=user_id)

    text = event.get_plaintext()[10:].strip().split(' ', 1)[-1].strip()
    if not text:
        logger.debug(f'broadcast no text: {user_id}, {event.get_plaintext()}')
        msg = f"广播消息: /broadcast [消息]\n机器人在所有共同QQ群里发送消息"
        await bot_send(bot, event, message=msg)
        return

    today_cnt = 0
    today = dt.utcnow().strftime('%Y-%m-%d')
    db_user_info = defaultdict(str)
    if user.user_info:
        db_user_info = json.loads(user.user_info)
        today_cnt = str(db_user_info.get(today) or 0)

    today_cnt = int(today_cnt) + 1
    # 每个用户 每天最多发送3次
    if today_cnt > 3:
        msg = f"每天最多发送3次广播消息"
        await bot_send(bot, event, message=msg)
        return

    db_user_info[today] = str(today_cnt)
    get_or_set_user(user_id=user_id, user_info=json.dumps(db_user_info))

    groups = get_all_group()
    g_id_lst = []
    group_id = (event.dict() or {}).get('group_id')
    for g in groups:
        if g.group_type != 'qq' or not g.bot_broadcast or not g.group_id or not g.member_id_list:
            continue
        if group_id and str(group_id) == str(g.group_id):
            continue
        if f',{user_id}' in g.member_id_list:
            g_id_lst.append(g.group_id)

    _msg = "设置: /广播消息 关闭\n发送: /broadcast 消息\n"
    msg = f"[CQ:at,qq={user_id}] 发送\n{text}\n"
    message = Message(_msg) + Message(msg)

    logger.debug(f'broadcast: {user_id}, {g_id_lst}\n{msg}')
    for g_id in g_id_lst:
        await bot_qq_send_group_msg(message, g_id)

    if not g_id_lst:
        msg = f"广播消息已发送至{len(g_id_lst)}个共同QQ群"
        await bot_send(bot, event, message=msg)


# 预留管理员使用
@on_command("bc", block=True, permission=permission.SUPERUSER).handle()
@check_session_handler
async def _broadcast(bot: Bot, event: Event):
    is_group = False
    cmd_lst = event.get_plaintext().strip().split()
    if 'g' in cmd_lst or 'group' in cmd_lst:
        is_group = True
    _id = ''
    for t in cmd_lst:
        if t.isdigit():
            _id = t
            break

    if not _id:
        return

    msg = event.get_plaintext().strip().split(_id, 1)[-1].strip()
    if not _id:
        return
    if is_group:
        await bot_qq_send_group_msg(msg, _id)
    else:
        await bot_qq_send_user_msg(msg, _id)


async def bot_qq_send_user_msg(msg, q_id):
    bots = get_bots()
    r = None
    for bot in bots.values():
        logger.debug(f'bot_qq_send_user_msg: {bot}')
        if isinstance(bot, QQBot):
            try:
                r = await bot.send_msg(message=msg, user_id=q_id)
                logger.debug(f'bot_qq_send_user_msg: {q_id}, {msg}\n{r}')
            except Exception as e:
                logger.error(e)
            return r


async def bot_qq_send_group_msg(msg, g_id):
    bots = get_bots()
    r = None
    for bot in bots.values():
        logger.debug(f'bot_qq_send_group_msg: {bot}')
        if isinstance(bot, QQBot):
            try:
                r = await bot.send_msg(message=msg, group_id=g_id)
                logger.debug(f'bot_qq_send_group_msg: {g_id}, {msg}\n{r}')
            except Exception as e:
                logger.error(e)
            return r
