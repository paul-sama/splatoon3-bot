import os
import functools
from datetime import datetime as dt

from nonebot import logger, get_driver, get_bots
from nonebot.adapters import Bot, Event
from nonebot.internal.matcher import Matcher
from nonebot.typing import T_State

# onebot11 协议
from nonebot.adapters.onebot.v11 import Bot as V11_Bot
from nonebot.adapters.onebot.v11 import MessageEvent as V11_ME
from nonebot.adapters.onebot.v11 import Message as V11_Msg
from nonebot.adapters.onebot.v11 import MessageSegment as V11_MsgSeg
from nonebot.adapters.onebot.v11 import PrivateMessageEvent as V11_PME
from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11_GME

# onebot12 协议
from nonebot.adapters.onebot.v12 import Bot as V12_Bot
from nonebot.adapters.onebot.v12 import MessageEvent as V12_ME
from nonebot.adapters.onebot.v12 import Message as V12_Msg
from nonebot.adapters.onebot.v12 import MessageSegment as V12_MsgSeg
from nonebot.adapters.onebot.v12 import ChannelMessageEvent as V12_CME
from nonebot.adapters.onebot.v12 import PrivateMessageEvent as V12_PME
from nonebot.adapters.onebot.v12 import GroupMessageEvent as V12_GME

# telegram 协议
from nonebot.adapters.telegram import Bot as Tg_Bot
from nonebot.adapters.telegram.event import MessageEvent as Tg_ME
from nonebot.adapters.telegram import MessageSegment as Tg_MsgSeg
from nonebot.adapters.telegram.event import PrivateMessageEvent as Tg_PME
from nonebot.adapters.telegram.event import GroupMessageEvent as Tg_GME
from nonebot.adapters.telegram.event import ChannelPostEvent as Tg_CME
from nonebot.adapters.telegram.message import File as Tg_File

# kook协议
from nonebot.adapters.kaiheila import Bot as Kook_Bot
from nonebot.adapters.kaiheila.event import MessageEvent as Kook_ME
from nonebot.adapters.kaiheila import MessageSegment as Kook_MsgSeg
from nonebot.adapters.kaiheila.event import PrivateMessageEvent as Kook_PME
from nonebot.adapters.kaiheila.event import ChannelMessageEvent as Kook_CME

# qq官方协议
from nonebot.adapters.qq import Bot as QQ_Bot
from nonebot.adapters.qq.event import MessageEvent as QQ_ME, GroupAtMessageCreateEvent
from nonebot.adapters.qq import MessageSegment as QQ_MsgSeg
from nonebot.adapters.qq.event import GroupAtMessageCreateEvent as QQ_GME  # 群艾特信息
from nonebot.adapters.qq.event import C2CMessageCreateEvent as QQ_C2CME  # Q私聊信息
from nonebot.adapters.qq.event import DirectMessageCreateEvent as QQ_PME  # 频道私聊信息
from nonebot.adapters.qq.event import AtMessageCreateEvent as QQ_CME  # 频道艾特信息

from .config import plugin_config
from .db_sqlite import get_user, get_all_group, set_db_info

from nonebot import require

require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import md_to_pic

INTERVAL = 10
BOT_VERSION = '1.5.2'
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

        if isinstance(bot, Tg_Bot):
            if 'reply_to_message_id' not in kwargs:
                rr = await bot.send(event, Tg_File.photo(img_data), reply_to_message_id=event.dict().get('message_id'))
            else:
                rr = await bot.send(event, Tg_File.photo(img_data))

        elif isinstance(bot, Kook_Bot):
            url = await bot.upload_file(img_data)
            if 'reply_to_message_id' not in kwargs:
                rr = await bot.send(event, Kook_MsgSeg.image(url), quote=event.dict().get('message_id'))
            else:
                rr = await bot.send(event, Kook_MsgSeg.image(url))

        elif isinstance(bot, QQ_Bot):
            if not isinstance(event, GroupAtMessageCreateEvent):
                await bot.send(event, message=QQ_MsgSeg.file_image(img_data))
            else:
                # 目前q群只支持url图片，得想办法上传图片获取url
                kook_bot = None
                for k, b in get_bots().items():
                    if isinstance(b, Kook_Bot):
                        kook_bot = b
                        break
                if kook_bot is not None:
                    # 使用kook的接口传图片
                    url = await kook_bot.upload_file(img_data)
                    await bot.send(event, message=QQ_MsgSeg.image(url))

        if not kwargs.get('skip_log_cmd'):
            await log_cmd_to_db(bot, event)
        return rr

    # 下面为文字消息
    if isinstance(bot, (Tg_Bot, Kook_Bot, QQ_Bot)):
        if 'group' in event.get_event_name() and 'reply_to_message_id' not in kwargs:
            kwargs['reply_to_message_id'] = event.dict().get('message_id')
        if 'group' in event.get_event_name():
            # /me 截断
            if '开放' in message and ': (+' not in message:
                coop_lst = message.split('2022-')[-1].split('2023-')[-1].strip().split('\n')
                message = message.split('2022-')[0].split('2023-')[0].strip() + '\n'
                for l in coop_lst:
                    if '打工次数' in l or '头目鲑鱼' in l:
                        message += '\n' + l
                message += '```'

    try:
        if isinstance(bot, Kook_Bot):
            r = await bot.send(event, message=Kook_MsgSeg.text(message), quote=event.dict().get('message_id'))
        elif isinstance(bot, QQ_Bot):
            r = await bot.send(event, message=QQ_MsgSeg.text(message))
        else:
            r = await bot.send(event, message, **kwargs)
    except Exception as e:
        r = None
        logger.exception(f'bot_send error: {e}, {message}')

    if not kwargs.get('skip_log_cmd'):
        await log_cmd_to_db(bot, event)
    return r


async def _check_session_handler(bot: Bot, event: Event, matcher: Matcher):
    """ nonebot 子依赖注入    Check if user has logged in."""
    # logger.info(f'_check_session_handler: {args}, {kwargs.keys()}, {func.__name__}')

    user = get_user(user_id=event.get_user_id())
    if not user or not user.session_token:
        _msg = ""
        if isinstance(bot, Tg_Bot):
            _msg = "Permission denied. /login first."
        elif isinstance(bot, (V11_Bot, V12_Bot, Kook_Bot, QQ_Bot)):
            _msg = '无权限查看，请先 /login 登录'
        await matcher.finish(_msg)


def get_event_info(bot, event):
    data = {'user_id': event.get_user_id()}
    _event = event.dict() or {}
    if isinstance(bot, Tg_Bot):
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
    elif isinstance(bot, Kook_Bot):
        data.update({
            'id_type': 'kk',
            'username': _event.get('event', {}).get('author', {}).get('username') or '',
        })
        if 'group' in event.get_event_name():
            data.update({
                'group_id': _event.get('target_id') or '',
                'group_name': _event.get('event', {}).get('channel_name', ''),
            })
    elif isinstance(bot, QQ_Bot):
        if _event.get('guild_id'):
            # qq 频道
            data.update({
                'id_type': 'qq',
                'username': _event.get('author', {}).get('username'),
            })

        else:
            # qq 群
            data.update({
                'id_type': 'qq',
                'username': 'QQ群',
            })
        if 'group' in event.get_event_name():
            data.update({
                'group_id': _event.get('guild_id') or _event.get('group_openid') or '',
                'group_name': '',
            })
    return data


async def log_cmd_to_db(bot, event, get_map=False):
    try:
        message = event.get_plaintext().strip()
        user_id = event.get_user_id()

        data = {'user_id': user_id, 'cmd': message}
        grp_cnt = ''
        data.update(get_event_info(bot, event))

        if get_map:
            data['map_cnt'] = 1
        else:
            data['cmd_cnt'] = 1

        set_db_info(**data)

        # log to tg channel
        str_grp = ''
        if data.get('group_id'):
            str_grp = f"群聊: #{data['id_type']}g{data['group_id']} ({data['group_name']}){grp_cnt}\n"
        if not str_grp:
            return

        text = f"#{data['id_type']}{data['user_id']}\n昵称:{data['username']}\n{str_grp}消息:{message}"
        await notify_tg_channel(text)

    except Exception as e:
        logger.warning(f'log_cmd_to_db error: {e}')


async def notify_tg_channel(_msg, _type='msg', **kwargs):
    # log to telegram
    notify_tg_bot_id = plugin_config.splatoon3_notify_tg_bot_id
    tg_channel_chat_id = plugin_config.splatoon3_tg_channel_msg_chat_id
    if _type == 'job':
        tg_channel_chat_id = plugin_config.splatoon3_tg_channel_job_chat_id

    if 'notify_tg_bot_id' in kwargs:
        notify_tg_bot_id = kwargs.get('notify_tg_bot_id')
    if 'tg_channel_chat_id' in kwargs:
        tg_channel_chat_id = kwargs.get('tg_channel_chat_id')

    # log to kook
    notify_kk_bot_id = plugin_config.splatoon3_notify_kk_bot_id
    kk_channel_chat_id = plugin_config.splatoon3_kk_channel_msg_chat_id
    if _type == 'job':
        kk_channel_chat_id = plugin_config.splatoon3_kk_channel_job_chat_id

    for bot in get_bots().values():
        if isinstance(bot, Tg_Bot):
            # 推送至tg
            if notify_tg_bot_id and tg_channel_chat_id and (bot.self_id == notify_tg_bot_id):
                await bot.send_message(tg_channel_chat_id, _msg)

        if isinstance(bot, Kook_Bot):
            # 推送至kook
            if notify_kk_bot_id and kk_channel_chat_id and (bot.self_id == notify_kk_bot_id):
                await bot.send_channel_msg(channel_id=kk_channel_chat_id, message=Kook_MsgSeg.KMarkdown(f"```\n{_msg}```"))
