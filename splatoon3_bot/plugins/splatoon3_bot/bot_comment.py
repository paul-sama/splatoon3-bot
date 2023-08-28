from datetime import datetime as dt

from nonebot import on_message, logger, on_regex
from nonebot.rule import to_me
from nonebot.adapters import Event, Bot

from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot as QQBot

from .db_sqlite import model_get_comment, model_add_comment
from .utils import bot_send


@on_regex("^[\\/.,，。]?留言[板]?$", block=True).handle()
async def _get_comment(bot: Bot, event: Event):
    msg = await get_comment_table(bot_id=bot.self_id)
    await bot_send(bot, event, msg, image_width=1000)


@on_message(block=False, rule=to_me()).handle()
async def _add_comment(bot: QQBot, event: GroupMessageEvent):
    message = event.get_plaintext().strip() or '*'
    if message[0] in ('/', '、', '.', '，', '。'):
        return

    _event = event.dict() or {}
    group_id = _event.get('group_id') or ''
    try:
        group_info = await bot.call_api('get_group_info', group_id=group_id)
    except Exception as e:
        logger.error(e)
        group_info = {}
    _dict = {
        'user_id': event.get_user_id(),
        'user_name': _event.get('sender', {}).get('nickname', ''),
        'group_id': group_id,
        'group_name': group_info.get('group_name', ''),
        'message': message,
    }
    model_add_comment(**_dict)

    msg = await get_comment_table(bot_id=bot.self_id)
    await bot_send(bot, event, msg, image_width=1000)


async def get_comment_table(bot_id):
    comment_lst = model_get_comment() or []

    msg = f'''#### 留言板({bot_id}) HKT {dt.now():%Y-%m-%d %H:%M:%S}
||||||
|---:||---:||---|
'''
    for c in comment_lst[-30:]:
        user_name = c.user_name or ''
        user_name += f''' |<img height="40" src="https://q1.qlogo.cn/g?b=qq&nk={c.user_id}&s=640"/>'''
        group_name = c.group_name or ''
        if group_name:
            group_name += f'''| <img height="40" src="https://p.qlogo.cn/gh/{c.group_id}/{c.group_id}/100"/>'''
        else:
            group_name = '|'
        cmt = c.message.strip().replace('\n', ' ').replace('|', '\|')
        msg += f"|{group_name}|{user_name}|{cmt}|\n"

    page = ''
    total_cnt = len(comment_lst)
    if total_cnt > 30:
        page_cnt = int(total_cnt / 30) + 1
        if total_cnt % 30 == 0:
            page_cnt -= 1
        page = f' | 页数: {page_cnt}/{page_cnt}'

    msg += '||\n\n 群聊 at机器人添加留言' + page
    # logger.info(f'get_comment_table: {msg}')
    return msg
