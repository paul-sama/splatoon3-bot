
import os
import functools

from nonebot import logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.telegram.message import File
from nonebot.adapters.onebot.v11 import Bot as QQBot, Message, MessageSegment
from .db_sqlite import get_user

from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import md_to_pic

INTERVAL = 10
BOT_VERSION = '0.9.8'
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
                if 'group' in event.get_event_name():
                    message += Message('\n群消息发送失败，bot被风控，请私聊使用或稍后再试')
                    await bot.send_private_msg(user_id=event.get_user_id(), message=message)

        elif isinstance(bot, TGBot):
            rr = await bot.send(event, File.photo(img_data))
        return rr

    if isinstance(bot, QQBot):
        message = message.replace('```', '').replace('\_', '_').strip().strip('`')
        if 'duration: ' in message or 'W1 ' in message:
            message = message.replace('`', '').replace('*', '')

        if 'group' in event.get_event_name():
            if '开放' in message:
                # /me 截断
                message = message.split('2022-')[0].split('2023-')[0].strip()
            if 'duration: ' in message:
                message, duration = message.split('duration: ')
                duration = duration.strip().split('\n')[0]
                message = message + f'\nduration: {duration}'
            if '\nW1' in message:
                message = message.split('\n\n')[0].strip()

            if 'reply_to_message_id' not in kwargs:
                message = Message(f"[CQ:reply,id={event.dict().get('message_id')}]" + message)

    elif isinstance(bot, TGBot):
        if 'group' in event.get_event_name() and 'reply_to_message_id' not in kwargs:
            kwargs['reply_to_message_id'] = event.dict().get('message_id')

    try:
        r = await bot.send(event, message, **kwargs)
    except Exception as e:
        r = None
        if 'group' in event.get_event_name() and isinstance(bot, QQBot):
            message += '\n\n' + '群消息发送失败，bot被风控，请私聊使用或稍后再试'
            try:
                await bot.send_private_msg(user_id=event.get_user_id(), message=message)
            except Exception as e:
                logger.error(message)
                logger.error(e)
            return r
        logger.error(f'bot_send error: {e}, {message}')

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
            if isinstance(bot, QQBot):
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
