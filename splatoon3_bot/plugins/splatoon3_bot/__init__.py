
from nonebot import logger, on_startswith, on_command, get_driver
from nonebot.adapters import Event, Bot
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.onebot.v11 import Bot as QQBot

from .db_sqlite import set_db_info
from .sp3msg import MSG_HELP, MSG_HELP_QQ
from .sp3job import cron_job
from .utils import bot_send

from .cmd_get import *
from .cmd_push import *
from .cmd_set import *


@on_startswith(("/", "、"), priority=1, block=False).handle()
async def all_command(bot: Bot, event: Event):
    data = {'user_id': event.get_user_id()}
    _event = event.dict() or {}
    if isinstance(bot, TGBot):
        data.update({
            'id_type': 'tg',
            'username': _event.get('from_', {}).get('username', ''),
            'first_name': _event.get('from_', {}).get('first_name', ''),
            'last_name': _event.get('from_', {}).get('last_name', ''),
            'cmd': event.get_plaintext().strip(),
        })
        if _event.get('chat', {}).get('type') == 'group':
            data.update({
                'group_id': _event['chat']['id'],
                'group_name': _event.get('chat', {}).get('title', ''),
            })
    elif isinstance(bot, QQBot):
        data.update({
            'id_type': 'qq',
            'username': _event.get('sender', {}).get('nickname', ''),
            'cmd': event.get_plaintext().strip(),
        })
        if _event.get('group_id'):
            try:
                group_info = await bot.call_api('get_group_info', group_id=_event['group_id'])
            except Exception as e:
                logger.error(e)
                group_info = {}
            data.update({
                'group_id': _event['group_id'],
                'group_name': group_info.get('group_name', ''),
            })
    set_db_info(**data)


@on_startswith(("/", "、"), priority=10).handle()
async def unknown_command(bot: Bot, event: Event):
    logger.info(f'unknown_command {event.get_event_name()}')
    if 'private' in event.get_event_name():
        _msg = "Sorry, I didn't understand that command. /help"
        if isinstance(bot, QQBot):
            _msg = '无效命令，输入 /help 查看帮助'
        logger.info(_msg)
        await bot.send(event, message=_msg)


@on_command("help", aliases={'h', '帮助', '说明', '文档'}, block=True).handle()
async def _help(bot: Bot, event: Event):
    if isinstance(bot, TGBot):
        await bot_send(bot, event, message=MSG_HELP, disable_web_page_preview=True)

    elif isinstance(bot, QQBot):
        await bot_send(bot, event, message=MSG_HELP_QQ)


@get_driver().on_startup
async def bot_on_start():
    version = utils.BOT_VERSION
    logger.info(f' bot start, version: {version} '.center(120, '-'))


@get_driver().on_bot_connect
async def _(bot: Bot):
    bot_type = 'Telegram' if isinstance(bot, TGBot) else 'QQ'
    logger.info(f' {bot_type} bot connect {bot.self_id} '.center(60, '-').center(120, ' '))

    job_id = f'sp3_cron_job_{bot.self_id}'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        cron_job, 'interval', minutes=1, id=job_id, args=[bot],
        misfire_grace_time=59, coalesce=True, max_instances=3
    )
