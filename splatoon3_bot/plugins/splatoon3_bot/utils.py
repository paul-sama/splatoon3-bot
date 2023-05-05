
import functools

from nonebot import logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.onebot.v11 import Bot as QQBot, Message
from .db_sqlite import get_user

INTERVAL = 10
BOT_VERSION = '0.0.3'


async def bot_send(bot: Bot, event: Event, message: str, **kwargs):
    if isinstance(bot, QQBot):
        message = message.replace('`', '').replace('*', '').replace('\_', '_').strip()
        if 'group' in event.get_event_name():
            # QQ机器人被风控，群聊消息太长会被吞掉，未被风控可取消截断
            message = message.split('duration')[0].split('2022-')[0].split('2023-')[0].strip()
            if '\nW1' in message:
                message = message.split('\n\n')[0].strip()
            message = Message(f"[CQ:at,qq={event.get_user_id()}]" + message)

    try:
        r = await bot.send(event, message, **kwargs)
    except Exception as e:
        r = None
        logger.error(message)
        logger.error(e)
        if 'group' in event.get_event_name():
            message = Message(f"[CQ:at,qq={event.get_user_id()}]" + '消息被风控，请稍后再试')
            r = await bot.send(event, message, **kwargs)

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

            await bot.send(event, message=_msg)
            return False

        result = await func(*args, **kwargs)
        return result

    return wrapper
