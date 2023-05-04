from nonebot import on_command, logger
from nonebot.adapters import Event, Bot

from .sp3bot import get_user_db_info, get_last_battle_or_coop, get_me, get_friends_msg
from .utils import bot_send, check_session_handler

__all__ = ['show_db_info', 'last', 'me']


@on_command("show_db_info", block=True).handle()
@check_session_handler
async def show_db_info(bot: Bot, event: Event):
    user_id = event.get_user_id()
    msg = get_user_db_info(user_id=user_id)

    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("last", block=True).handle()
@check_session_handler
async def last(bot: Bot, event: Event):
    user_id = event.get_user_id()

    msg = await get_last_battle_or_coop(user_id)
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("me", block=True).handle()
@check_session_handler
async def me(bot: Bot, event: Event):
    user_id = event.get_user_id()

    msg = get_me(user_id)
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("friends", block=True).handle()
@check_session_handler
async def me(bot: Bot, event: Event):
    msg = get_friends_msg(event.get_user_id())
    await bot_send(bot, event, msg, parse_mode='Markdown')
