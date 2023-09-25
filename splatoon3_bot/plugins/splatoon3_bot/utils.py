
import os
import functools

from nonebot import logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.telegram.message import File
from nonebot.adapters.onebot.v11 import Bot as QQBot, Message, MessageSegment
from nonebot.adapters.onebot.v12 import Bot as WXBot, Message, MessageSegment as WXMsgSeg
from .db_sqlite import get_user, get_all_group, set_db_info

from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import md_to_pic

INTERVAL = 10
BOT_VERSION = '1.3.3'
DIR_RESOURCE = f'{os.path.abspath(os.path.join(__file__, os.pardir))}/resource'


async def bot_send(bot: Bot, event: Event, message: str, **kwargs):

    img_data = ''
    if message and message.strip().startswith('####'):
        width = 1000
        if 'image_width' in kwargs:
            width = kwargs.get('image_width')
        # 打工
        if 'W1 ' in message and 'duration: ' not in message:
            width = 570
        img_data = await md_to_pic(message, width=width, css_path=f'{DIR_RESOURCE}/md.css')

    if kwargs.get('photo'):
        img_data = kwargs.get('photo')

    if img_data:
        rr = None
        if isinstance(bot, QQBot):
            img = MessageSegment.image(file=img_data, cache=False)

            msg = ''
            if 'group' in event.get_event_name() and 'reply_to_message_id' not in kwargs:
                msg = f"[CQ:reply,id={event.dict().get('message_id')}]"
            message = Message(msg) + Message(img)
            try:
                rr = await bot.send(event, message=message)
            except Exception as e:
                logger.warning(f'QQBot send error: {e}')

        elif isinstance(bot, TGBot):
            rr = await bot.send(event, File.photo(img_data))

        elif isinstance(bot, WXBot):
            # onebot12协议需要先上传文件获取file_id后才能发送图片
            try:
                resp = await bot.upload_file(type="data", name="temp.png", data=img_data)
                file_id = resp["file_id"]
                if file_id:
                    await bot.send(event, message=WXMsgSeg.image(file_id=file_id))
            except Exception as e:
                logger.warning(f"QQBot send error: {e}")

        if not kwargs.get('skip_log_cmd'):
            await log_cmd_to_db(bot, event)
        return rr

    if isinstance(bot, (QQBot, WXBot)):
        message = message.replace('```', '').replace('\_', '_').strip().strip('`')
        if 'duration: ' in message or 'W1 ' in message:
            message = message.replace('`', '').replace('*', '')

        if 'group' in event.get_event_name():
            if '开放' in message and ': (+' not in message:
                coop_lst = message.split('2022-')[-1].split('2023-')[-1].strip().split('\n')
                # /me 截断
                message = message.split('2022-')[0].split('2023-')[0].strip() + '\n'
                for l in coop_lst:
                    if '打工次数' in l or '头目鲑鱼' in l:
                        message += '\n' + l

            if 'duration: ' in message:
                message, duration = message.split('duration: ')
                duration = duration.strip().split('\n')[0]
                message = message + f'\nduration: {duration}'
            if '\nW1' in message:
                message = message.split('\n\n')[0].strip()

            if 'reply_to_message_id' not in kwargs and isinstance(bot, QQBot):
                message = Message(f"[CQ:reply,id={event.dict().get('message_id')}]" + message)

    elif isinstance(bot, TGBot):
        if 'group' in event.get_event_name() and 'reply_to_message_id' not in kwargs:
            kwargs['reply_to_message_id'] = event.dict().get('message_id')

    try:
        if isinstance(bot, WXBot):
            r = await bot.send(event, message)
        else:
            r = await bot.send(event, message, **kwargs)
    except Exception as e:
        r = None
        logger.exception(f'bot_send error: {e}, {message}')

    if not kwargs.get('skip_log_cmd'):
        await log_cmd_to_db(bot, event)
    return r


def check_session_handler(func):
    """Check if user has logged in."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # logger.info(f'check_session_handler: {args}, {kwargs.keys()}, {func.__name__}')
        bot = kwargs.get('bot')
        if not isinstance(bot, Bot):
            logger.error(f'wrapper: {args[0]} is not Bot')
            return

        event = kwargs.get('event')
        user = get_user(user_id=event.get_user_id())
        if not user or not user.session_token:
            _msg = "Permission denied. /login first."
            if isinstance(bot, (QQBot, WXBot)):
                _msg = '无权限查看，请先 /login 登录'

            matcher = kwargs.get('matcher')
            if matcher:
                await matcher.finish(_msg)
                return False

            if isinstance(bot, QQBot):
                await bot.send(event, message=_msg, reply_message=True)
                return False
            await bot.send(event, message=_msg)
            return False

        result = await func(*args, **kwargs)
        return result

    return wrapper


async def log_cmd_to_db(bot, event):
    try:
        message = event.get_plaintext().strip()
        _event = event.dict() or {}

        data = {'user_id': event.get_user_id(), 'cmd': message}
        if isinstance(bot, QQBot):
            data.update({
                'id_type': 'qq',
                'username': _event.get('sender', {}).get('nickname', '')
            })
            group_id = _event.get('group_id')
            if group_id:
                group_name = ''
                group_lst = get_all_group()
                for g in group_lst:
                    if str(g.group_id) == str(group_id):
                        group_name = g.group_name
                        break
                data.update({
                    'group_id': group_id,
                    'group_name': group_name,
                })

        elif isinstance(bot, TGBot):
            name = _event.get('from_', {}).get('first_name', '')
            if _event.get('from_', {}).get('last_name'):
                name += ' ' + _event.get('from_', {}).get('last_name')
            if not name:
                name = _event.get('from_', {}).get('username') or ''

            data.update({
                'id_type': 'tg',
                'username': name,
                'first_name': _event.get('from_', {}).get('first_name', ''),
                'last_name': _event.get('from_', {}).get('last_name', ''),
            })
            if 'group' in _event.get('chat', {}).get('type', ''):
                data.update({
                    'group_id': _event['chat']['id'],
                    'group_name': _event.get('chat', {}).get('title', ''),
                })

        elif isinstance(bot, WXBot):
            user_info = await bot.get_user_info(user_id=event.get_user_id())
            if not user_info:
                logger.info(f'get_user_info wx failed, {event.get_user_id()}')
                return
            data.update({
                'id_type': 'wx',
                'username': user_info.get('user_name', '')
            })
            group_id = _event.get('group_id')
            if group_id:
                group_info = await bot.get_group_info(group_id=group_id)
                data.update({
                    'group_id': group_id,
                    'group_name': group_info.get('group_name', ''),
                })

        set_db_info(**data)

    except Exception as e:
        logger.warning(f'log_cmd_to_db error: {e}')
