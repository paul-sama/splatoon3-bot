import json

from nonebot import logger, on_startswith, on_command, get_driver, get_bots
from nonebot.adapters import Event, Bot
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.onebot.v11 import Bot as QQBot
from nonebot.adapters.onebot.v12 import Bot as WXBot

# kook协议
from nonebot.adapters.kaiheila import Bot as KookBot
from nonebot.adapters.kaiheila.event import MessageEvent as Kook_ME
from nonebot.adapters.kaiheila import MessageSegment as Kook_MsgSeg
from nonebot.adapters.kaiheila.event import PrivateMessageEvent as Kook_PME
from nonebot.adapters.kaiheila.event import ChannelMessageEvent as Kook_CME

from nonebot.message import event_preprocessor
from nonebot.permission import SUPERUSER

from .db_sqlite import set_db_info
from .sp3msg import MSG_HELP, MSG_HELP_QQ
from .sp3job import cron_job
from .utils import bot_send, notify_tg_channel, get_event_info

from .cmd_get import *
from .cmd_push import *
from .cmd_set import *
from .cmd_broadcast import *
from .bot_comment import *


@on_startswith(("/", "、"), priority=1, block=False).handle()
async def all_command(bot: Bot, event: Event):
    data = {'user_id': event.get_user_id()}
    data.update(get_event_info(bot, event))
    set_db_info(**data)


@on_startswith(("/", "、"), priority=10).handle()
async def unknown_command(bot: Bot, event: Event):
    logger.info(f'unknown_command {event.get_event_name()}')
    if 'private' in event.get_event_name():
        _msg = "Sorry, I didn't understand that command. /help"
        if isinstance(bot, (QQBot, WXBot)):
            _msg = '无效命令，输入 /help 查看帮助'
        logger.info(_msg)
        await bot.send(event, message=_msg)


@on_command("help", aliases={'h', '帮助', '说明', '文档'}, block=True).handle()
async def _help(bot: Bot, event: Event):
    if isinstance(bot, TGBot):
        await bot_send(bot, event, message=MSG_HELP, disable_web_page_preview=True)

    elif isinstance(bot, (QQBot, WXBot, KookBot)):
        msg = MSG_HELP_QQ
        await bot_send(bot, event, message=msg)


@get_driver().on_startup
async def bot_on_start():
    version = utils.BOT_VERSION
    logger.info(f' bot start, version: {version} '.center(120, '-'))


@get_driver().on_shutdown
async def bot_on_shutdown():
    version = utils.BOT_VERSION
    logger.info(f' bot shutdown, version: {version} '.center(120, 'x'))
    bots = get_bots()
    logger.info(f'bot: {bots}')
    for k in bots.keys():
        job_id = f'sp3_cron_job_{k}'
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f'remove job {job_id}!')


@get_driver().on_bot_connect
async def _(bot: Bot):
    bot_type = 'Telegram'
    if isinstance(bot, QQBot):
        bot_type = 'QQ'
    elif isinstance(bot, WXBot):
        bot_type = 'WeChat'
    elif isinstance(bot, KookBot):
        bot_type = 'Kook'

    logger.info(f' {bot_type} bot connect {bot.self_id} '.center(60, '-').center(120, ' '))

    job_id = f'sp3_cron_job_{bot.self_id}'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f'remove job {job_id} first')

    scheduler.add_job(
        cron_job, 'interval', minutes=1, id=job_id, args=[bot],
        misfire_grace_time=59, coalesce=True, max_instances=1
    )
    logger.info(f'add job {job_id}')

    if bot_type == 'QQ':
        text = f'bot {bot_type}: {bot.self_id} online ~'
        await notify_tg_channel(text)


@get_driver().on_bot_disconnect
async def _(bot: Bot):
    bot_type = 'Telegram'
    if isinstance(bot, QQBot):
        bot_type = 'QQ'
    elif isinstance(bot, WXBot):
        bot_type = 'WeChat'
    elif isinstance(bot, KookBot):
        bot_type = 'Kook'

    text = f'bot {bot_type}: {bot.self_id} disconnect !!!!!!!!!!!!!!!!!!!'
    await notify_tg_channel(text)


@event_preprocessor
async def tg_private_msg(bot: TGBot, event: Event):
    try:
        user_id = event.get_user_id()
        message = event.get_plaintext().strip()
    except:
        user_id = ''
        message = ''

    _event = event.dict() or {}
    logger.debug(_event)
    if user_id and message and 'group' not in _event.get('chat', {}).get('type', ''):
        logger.info(f'tg_private_msg {user_id} {message}')

        name = _event.get('from_', {}).get('first_name', '')
        if _event.get('from_', {}).get('last_name', ''):
            name += ' ' + _event.get('from_', {}).get('last_name', '')
        if not name:
            name = _event.get('from_', {}).get('username', '')

        text = f"#tg{user_id}\n昵称:{name}\n消息:{message}"
        await notify_tg_channel(text)


@event_preprocessor
async def kk_private_msg(bot: KookBot, event: Event):
    try:
        user_id = event.get_user_id()
        message = event.get_plaintext().strip()
    except:
        user_id = ''
        message = ''

    if user_id == 'SYSTEM' and message == "[系统消息]":
        return

    _event = event.dict() or {}
    logger.debug(_event)
    if user_id and message and 'group' not in event.get_event_name():
        logger.info(f'kk_private_msg {user_id} {message}')

        name = _event.get('event', {}).get('author', {}).get('username') or ''
        text = f"#kk{user_id}\n昵称:{name}\n消息:{message}"
        await notify_tg_channel(text)


@on_command("admin", block=True, permission=SUPERUSER).handle()
async def admin_cmd(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text().strip()[6:].strip()
    logger.info(f'admin: {plain_text}')
    if plain_text == 'get_event_top':
        from .scripts.top_player import task_get_league_player
        from .splat import Splatoon, get_or_set_user
        user_id = event.get_user_id()
        user = get_or_set_user(user_id=user_id)
        splt = Splatoon(user_id, user.session_token)
        await task_get_league_player(splt)

    elif plain_text == 'get_user_friend':
        from .scripts.user_friend import task_get_user_friend
        await task_get_user_friend(False)

    elif plain_text.startswith('set'):
        _msg = plain_text[3:].strip() or ''
        _lst = _msg.split(' ')
        if not _msg or len(_lst) != 3:
            await bot_send(bot, event, message='admin set user_id key value 参数错误')
            return
        from .db_sqlite import get_user, get_or_set_user
        u_id, key, val = _lst
        user = get_user(user_id=u_id)
        if not user:
            await bot_send(bot, event, message=f'no user: {u_id}')
            return
        if key in ('push', ):
            val = int(val)
        _d = {'user_id': u_id, key: val}
        get_or_set_user(**_d)
        await bot_send(bot, event, message=f'set {user.username}, {user.nickname}, {key} = {val}')

    elif plain_text == 'get_push':
        from .db_sqlite import get_all_user
        users = get_all_user()
        msg = ''
        for u in users:
            if not u.push:
                continue
            msg += f'{u.id:>4}, {u.push_cnt:>3}, {u.username}, {u.nickname}\n'
        msg = f'```\n{msg}```' if msg else 'no data'
        await bot_send(bot, event, message=msg, parse_mode='Markdown')
