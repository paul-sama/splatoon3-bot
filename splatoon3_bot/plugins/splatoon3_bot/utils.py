
from nonebot import logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.onebot.v11 import Bot as QQBot, Message
from .db_sqlite import get_user

INTERVAL = 10
BOT_VERSION = '0.0.1'


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


async def check_user_login(bot: Bot, event: Event) -> bool:
    user = get_user(user_id=event.get_user_id())
    if not user or not user.session_token:
        if isinstance(bot, TGBot):
            await bot.send(event, message="Permission denied. /login first.")
        elif isinstance(bot, QQBot):
            await bot.send(event, message="无权限查看，请先 /login 登录")
        return False
    return True
