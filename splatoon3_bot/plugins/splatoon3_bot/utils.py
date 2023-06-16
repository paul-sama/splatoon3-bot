
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
BOT_VERSION = '0.2.8'
DIR_RESOURCE = f'{os.path.abspath(os.path.join(__file__, os.pardir))}/resource'


async def bot_send(bot: Bot, event: Event, message: str, **kwargs):

    if message and message.strip().startswith('####'):
        tmp_file = await get_pic_from_md_msg(message)
        if tmp_file:
            if isinstance(bot, TGBot):
                await bot.send(event, File.photo(tmp_file))
            elif isinstance(bot, QQBot):
                img = MessageSegment.image('file:///' + tmp_file)
                await bot.send(event, message=Message(img))
            return

    if kwargs.get('photo'):
        img_data = kwargs.get('photo')
        if isinstance(bot, QQBot):
            img = MessageSegment.image(file=img_data, cache=False)

            msg = ''
            if 'group' in event.get_event_name():
                user_id = str(event.get_user_id())
                msg = f"[CQ:at,qq={user_id}]"
            message = Message(msg) + Message(img)
            try:
                await bot.send(event, message=message)
            except Exception as e:
                logger.error(f'QQBot send error: {e}')

        elif isinstance(bot, TGBot):
            await bot.send(event, File.photo(img_data))
        return

    if isinstance(bot, QQBot):
        message = message.replace('`', '').replace('*', '').replace('\_', '_').strip()
        if 'group' in event.get_event_name():
            # QQ机器人被风控，群聊消息太长会被吞掉，未被风控可取消截断
            message = message.replace('https://github.com/paul-sama/splatoon3-bot', '')
            if '开放' in message:
                message = message.split('2022-')[0].split('2023-')[0].strip()
            if 'duration: ' in message:
                message, duration = message.split('duration: ')
                duration = duration.strip().split('\n')[0]
                message = message + f'\nduration: {duration}'
            if '\nW1' in message:
                message = message.split('\n\n')[0].strip()
            message = Message(f"[CQ:at,qq={event.get_user_id()}]" + message)

    elif isinstance(bot, TGBot):
        if 'group' in event.get_event_name() and 'reply_to_message_id' not in kwargs:
            kwargs['reply_to_message_id'] = event.dict().get('message_id')

    try:
        r = await bot.send(event, message, **kwargs)
    except Exception as e:
        r = None
        logger.error(message)
        logger.error(e)
        if 'group' in event.get_event_name():
            message += '\n\n' + '群消息发送失败，bot被风控，请私聊使用或稍后再试'
            try:
                await bot.send_private_msg(user_id=event.get_user_id(), message=message)
            except Exception as e:
                logger.error(e)

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


async def get_pic_from_md_msg(message):
    import PIL.Image, uuid, os, io

    path_folder = f'{DIR_RESOURCE}/msg_img'
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)

    pic_bytes = await md_to_pic(message, width=1000, css_path=f'{DIR_RESOURCE}/md.css')
    if pic_bytes:
        tmp_file = f'{path_folder}/{uuid.uuid4().hex}.png'
        a = PIL.Image.open(io.BytesIO(pic_bytes))
        a.save(tmp_file, format="PNG")
        logger.debug(f'tmp_file: {tmp_file}')
        return tmp_file
