from typing import Union
from datetime import datetime as dt

from nonebot import on_message, logger, on_regex
from nonebot.rule import to_me
from nonebot.adapters import Event, Bot

from .db_sqlite import model_get_comment, model_add_comment
from .utils import bot_send, V11_Bot, V12_Bot,V11_GME,V12_GME
from .splatnet_image import get_app_screenshot


@on_regex("^http.*$").handle()
async def _http(bot: V11_Bot, event: Event):
    _msg = event.get_plaintext().strip()
    logger.info(f'get msg http: {_msg}')
    if 'twitter.com' in _msg or 'x.com' in _msg:
        url = _msg.split(' ')[0]
        try:
            pic = await get_app_screenshot('', url=url)
            await bot_send(bot, event, '', photo=pic)
        except Exception as e:
            logger.warning(f'get http ss: {e}')


@on_regex("^[\\/.,，。]?留言[板]?$", priority=10, block=True).handle()
async def _get_comment(bot: Bot, event: Event):
    msg = await get_comment_table(bot)
    await bot_send(bot, event, msg, image_width=1000)


# @on_message(block=False, rule=to_me()).handle()
# async def _add_comment(bot: Union[V11_Bot, V12_Bot], event: Union[V11_GME, V12_GME]):
#     message = event.get_plaintext().strip() or '*'
#     if message[0] in ('/', '、', '.', '，', '。') or message in ('*', '工', '全部工', '图', '全部图', '留言', '留言板'):
#         return
#
#     _event = event.dict() or {}
#     logger.debug(f'comment_event: {_event}')
#     if isinstance(bot, V11_Bot):
#         group_id = _event.get('group_id') or ''
#         try:
#             group_info = await bot.call_api('get_group_info', group_id=group_id)
#         except Exception as e:
#             logger.error(e)
#             group_info = {}
#         _dict = {
#             'user_id': event.get_user_id(),
#             'user_name': _event.get('sender', {}).get('nickname', ''),
#             'group_id': group_id,
#             'group_name': group_info.get('group_name', ''),
#             'message': message,
#         }
#     else:
#         user_id = event.get_user_id()
#         user_info = await bot.get_user_info(user_id=event.get_user_id())
#         if not user_info:
#             logger.info(f'get_user_info wx failed, {event.get_user_id()}')
#             return
#         group_id = _event.get('group_id')
#         group_info = await bot.get_group_info(group_id=group_id) or {}
#
#         _dict = {
#             'bot_type': 'wx',
#             'user_id': user_id,
#             'user_icon': (user_info.get('wx') or {}).get('avatar') or '',
#             'user_name': user_info.get('user_name', ''),
#             'group_id': group_id,
#             'group_name': group_info.get('group_name', ''),
#             'group_icon': (group_info.get('wx') or {}).get('avatar') or '',
#             'message': message,
#         }
#
#     model_add_comment(**_dict)
#
#     msg = await get_comment_table(bot)
#     await bot_send(bot, event, msg, image_width=1000)


async def get_comment_table(bot):
    comment_lst = model_get_comment() or []

    msg = f'''#### 留言板 HKT {dt.now():%Y-%m-%d %H:%M:%S}
||||||
|---:||---:||---|
'''
    for c in comment_lst[-30:]:
        user_name = c.user_name or ''
        user_name = user_name.replace('`', '&#96;').replace('|', '&#124;')
        u_icon = f"https://q1.qlogo.cn/g?b=qq&nk={c.user_id}&s=640"
        if c.bot_type == 'wx':
            u_icon = c.user_icon or ''
            user_name = f"<span style='color:green'>{user_name}</span>"
        user_name += f''' |<img height="40" src="{u_icon}"/>'''
        group_name = c.group_name or ''
        group_name = group_name.replace('`', '&#96;').replace('|', '&#124;')
        if group_name:
            g_icon = f"https://p.qlogo.cn/gh/{c.group_id}/{c.group_id}/100"
            if c.bot_type == 'wx':
                g_icon = c.group_icon or ''
                group_name = f"<span style='color:green'>{group_name}</span>"
            group_name += f'''| <img height="40" src="{g_icon}"/>'''
        else:
            group_name = '|'
        cmt = c.message.strip().replace('\n', ' ').replace('|', '\|')
        # if isinstance(bot, WXBot):
        #     cmt = cmt[:30]
        msg += f"|{group_name}|{user_name}|{cmt}|\n"

    page = ''
    total_cnt = len(comment_lst)
    if total_cnt > 30:
        page_cnt = int(total_cnt / 30) + 1
        if total_cnt % 30 == 0:
            page_cnt -= 1
        page = f' | 页数: {page_cnt}/{page_cnt}. 所有留言可在腾讯文档查看.'

    msg += '||\n\n 群聊 at机器人添加留言' + page
    # logger.info(f'get_comment_table: {msg}')
    return msg
