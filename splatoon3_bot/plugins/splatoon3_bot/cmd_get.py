from nonebot import on_command, logger
from nonebot.adapters import Event, Bot

from .sp3bot import get_user_db_info, get_last_battle_or_coop, get_me
from .utils import bot_send, check_user_login

__all__ = ['show_db_info', 'last', 'me']


@on_command("show_db_info", block=True).handle()
async def show_db_info(bot: Bot, event: Event):
    if not await check_user_login(bot, event):
        return
    user_id = event.get_user_id()
    msg = get_user_db_info(user_id=user_id)

    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("last", block=True).handle()
async def last(bot: Bot, event: Event):
    if not await check_user_login(bot, event):
        return
    user_id = event.get_user_id()

    msg = await get_last_battle_or_coop(user_id)
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("me", block=True).handle()
async def me(bot: Bot, event: Event):
    if not await check_user_login(bot, event):
        return
    user_id = event.get_user_id()

    msg = get_me(user_id)
    logger.info(msg)
    await bot_send(bot, event, msg, parse_mode='Markdown')
