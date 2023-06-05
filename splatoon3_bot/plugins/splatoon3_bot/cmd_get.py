from nonebot import on_command, logger
from nonebot.adapters import Event, Bot

from .sp3bot import (
    get_user_db_info, get_last_battle_or_coop, get_me, get_friends_msg, get_ns_friends_msg, get_x_top_msg,
    get_my_schedule_msg, get_screenshot_image
)
from .utils import bot_send, check_session_handler

__all__ = ['show_db_info', 'last', 'me']


@on_command("show_db_info", aliases={'sdi'}, block=True).handle()
@check_session_handler
async def show_db_info(bot: Bot, event: Event):
    user_id = event.get_user_id()
    msg = get_user_db_info(user_id=user_id)

    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("last", block=True).handle()
@check_session_handler
async def last(bot: Bot, event: Event):
    user_id = event.get_user_id()

    get_battle = False
    get_coop = False
    get_pic = False
    idx = 0
    cmd_message = event.get_plaintext()[5:].strip()
    logger.debug(f'last: {cmd_message}')
    if cmd_message:
        cmd_lst = cmd_message.split()
        if 'b' in cmd_lst or 'battle' in cmd_lst:
            get_battle = True
        if 'c' in cmd_lst or 'coop' in cmd_lst:
            get_coop = True
        if 'p' in cmd_lst or 'pic' in cmd_lst:
            get_pic = True
        for cmd in cmd_lst:
            if cmd.isdigit():
                idx = int(cmd) - 1
                break

    msg = await get_last_battle_or_coop(user_id, get_battle=get_battle, get_coop=get_coop, get_pic=get_pic, idx=idx)
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("me", block=True).handle()
@check_session_handler
async def me(bot: Bot, event: Event):
    user_id = event.get_user_id()

    msg = get_me(user_id)
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("friends", block=True).handle()
@check_session_handler
async def friends(bot: Bot, event: Event):
    msg = get_friends_msg(event.get_user_id())
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("ns_friends", block=True).handle()
@check_session_handler
async def ns_friends(bot: Bot, event: Event):
    msg = get_ns_friends_msg(event.get_user_id())
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("x_top", block=True).handle()
async def x_top(bot: Bot, event: Event):
    msg = get_x_top_msg()
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("my_schedule", block=True).handle()
async def schedule(bot: Bot, event: Event):
    msg = get_my_schedule_msg(event.get_user_id())
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("screen_shot", aliases={'ss'}, block=True).handle()
async def screen_shot(bot: Bot, event: Event):
    key = ''
    if ' ' in event.get_plaintext():
        key = event.get_plaintext().split(' ', 1)[1].strip()
    img = await get_screenshot_image(event.get_user_id(), key=key)
    await bot_send(bot, event, message='', photo=img)
