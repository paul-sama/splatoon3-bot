import os
import json
from collections import defaultdict
from datetime import datetime as dt

from nonebot import on_command, logger
from nonebot.adapters import Event, Bot
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.telegram.message import File
from nonebot.adapters.onebot.v11 import Bot as QQBot
from nonebot.typing import T_State

from .db_sqlite import set_db_info, get_user, get_or_set_user
from .sp3iksm import log_in, login_2, A_VERSION
from .splat import Splatoon
from .sp3bot import get_last_battle_or_coop
from .sp3job import get_post_stat_msg, update_s3si_ts, thread_function, threading, asyncio
from .utils import bot_send, check_session_handler
from .scripts.report import get_report


__all__ = ['login', 'login_id', 'clear_db_info', 'set_db_info', 'get_set_battle_info']
MSG_PRIVATE = '请添加机器人为好友再私聊完成登录操作'


matcher_login = on_command("login", block=True)


@matcher_login.handle()
async def login(bot: Bot, event: Event, state: T_State):
    if 'group' in event.get_event_name():
        await matcher_login.finish(MSG_PRIVATE, reply_message=True)
        return

    u = get_or_set_user(user_id=event.get_user_id())
    if u and u.session_token:
        msg = '用户已经登录\n如需重新登录或切换账号请继续下面操作\n登出或清空账号数据 /clear_db_info'
        await bot_send(bot, event, msg)

    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path = f'{dir_path}/resource/sp3bot-login.gif'
    if isinstance(bot, TGBot):
        try:
            logger.info(f'img_path: {img_path}')
            await bot.send(event, File.animation(img_path))
        except Exception as e:
            logger.error(f'login error: {e}')

    url, auth_code_verifier = log_in(A_VERSION)
    state['auth_code_verifier'] = auth_code_verifier
    logger.info(f'get login url: {url}')
    logger.info(f'auth_code_verifier: {auth_code_verifier}')
    if url:
        msg = ''
        if isinstance(bot, TGBot):
            msg = f'''
Navigate to this URL in your browser:
{url}
Log in, right click the "Select this account" button, copy the link address, and paste below. (Valid for 2 minutes)
            '''
        elif isinstance(bot, QQBot):
            msg = f'''在浏览器中打开下面链接
{url}
登陆后，右键账号后面的红色按钮，复制链接后发送给机器人 (两分钟内有效)
'''
        if msg:
            await bot.send(event, message=msg)


@matcher_login.receive('id')
async def login_id(bot: Bot, event: Event, state: T_State):
    text = event.get_plaintext()

    auth_code_verifier = state.get('auth_code_verifier')

    err_msg = '登录失败，请 /login 重试, 复制新链接'
    if not text or len(text) < 500 or not text.startswith('npf') or not auth_code_verifier:
        logger.info(err_msg)
        await bot.send(event, message=err_msg)
        return

    session_token = login_2(use_account_url=text, auth_code_verifier=auth_code_verifier)
    if session_token == 'skip':
        logger.info(err_msg)
        await bot.send(event, message=err_msg)
        return
    logger.info(f'session_token: {session_token}')
    user_id = event.get_user_id()
    data = {
        'session_token': session_token,
        'user_id': user_id,
        'id_type': 'tg' if isinstance(bot, TGBot) else 'qq',
    }
    if isinstance(bot, TGBot):
        data['report_type'] = 1
    set_db_info(**data)
    '''
/set_lang - set language, default(zh-CN) 默认中文
'''
    msg = f"""
Login success! Bot now can get your splatoon3 data from SplatNet.
/me - show your info
/last - show the latest battle or coop
/start_push - start push mode
/set_api_key - set stat.ink api_key, bot will sync your data to stat.ink
"""
    if isinstance(bot, QQBot):
        msg = f"""
登录成功！机器人现在可以从App获取你的数据。
/me - 显示你的信息
/friends - 显示在线的喷喷好友
/last - 显示最近一场对战或打工
/start_push - 开启推送模式
/set_api_key - 设置 api_key, 同步数据到 https://stat.ink
"""
    await bot.send(event, message=msg)

    user = get_user(user_id=user_id)
    Splatoon(user.id, user.session_token).set_gtoken_and_bullettoken()


@on_command("clear_db_info", block=True).handle()
async def clear_db_info(bot: Bot, event: Event):

    if 'group' in event.get_event_name():
        await bot_send(bot, event, '请私聊机器人', parse_mode='Markdown')
        return

    user_id = event.get_user_id()

    get_or_set_user(
        user_id=user_id,
        gtoken=None,
        bullettoken=None,
        session_token=None,
        session_token_2=None,
        push=False,
        push_cnt=0,
        api_key=None,
        acc_loc=None,
        user_info=None,
    )

    msg = "All your data cleared! 已清空账号数据!"
    logger.info(msg)
    await bot.send(event, message=msg)


matcher_set_battle_info = on_command("set_battle_info", aliases={'sbi'}, block=True)


@matcher_set_battle_info.handle()
@check_session_handler
async def set_battle_info(bot: Bot, event: Event, matcher: matcher_set_battle_info):
    if isinstance(bot, QQBot) and 'group' in event.get_event_name():
        await matcher_set_battle_info.finish(MSG_PRIVATE)
        return

    msg = '''
set battle info, default 1): show name
1 - name
2 - weapon
3 - name (weapon)
4 - weapon (name)
5 - weapon (name) byname
6 - weapon (name)#nameId byname
'''
    if isinstance(bot, QQBot):
        msg = '设置对战显示信息， 默认为 1): 名字' + msg.split('show name')[-1]
    await bot_send(bot, event, message=msg)


@matcher_set_battle_info.receive('id')
async def get_set_battle_info(bot: Bot, event: Event):
    try:
        text = int(event.get_plaintext())
        if not text or text not in range(1, 7):
            raise ValueError()
    except:
        text = 1

    await bot.send(event, message=f'set type: {text}')

    user_id = event.get_user_id()
    user = get_or_set_user(user_id=user_id)
    db_user_info = defaultdict(str)
    if user and user.user_info:
        db_user_info = json.loads(user.user_info)
    db_user_info['battle_show_type'] = str(text)
    get_or_set_user(user_id=user_id, user_info=json.dumps(db_user_info))
    msg = await get_last_battle_or_coop(user_id, get_battle=True)
    await bot_send(bot, event, message=msg, parse_mode='Markdown')


matcher_set_api_key = on_command("set_api_key", block=True)


@matcher_set_api_key.handle()
@check_session_handler
async def set_api_key(bot: Bot, event: Event, matcher: matcher_set_api_key):
    if 'group' in event.get_event_name():
        await matcher_set_battle_info.finish(MSG_PRIVATE)
        return

    msg = '''Please copy you api_key from https://stat.ink/profile then paste below'''
    if isinstance(bot, QQBot):
        msg = '''请从 https://stat.ink/profile 页面复制你的 api_key 后发送给机器人
注册stat.ink账号后，无需其他操作，设置api_key
机器人会每2小时检查并同步你的数据到 stat.ink (App最多保存最近50场对战数据)
        '''
    await bot_send(bot, event, message=msg)


@matcher_set_api_key.receive('id')
async def get_set_api_key(bot: Bot, event: Event, matcher: matcher_set_api_key):
    api_key = event.get_plaintext().strip()

    if len(api_key) != 43:
        await matcher_set_api_key.finish("错误信息")
        return

    logger.info(f'set_api_key: {api_key}')
    get_or_set_user(user_id=event.get_user_id(), api_key=api_key)

    msg = f'''set_api_key success, bot will check every 2 hours and post your data to stat.ink.
first sync will be in minutes.
    '''
    if isinstance(bot, QQBot):
        msg = f'''设置成功，机器人会每2小时检查一次并同步你的数据到 stat.ink 第一次同步会即刻开始。'''
    await bot_send(bot, event, message=msg)

    update_s3si_ts()
    user_id = event.get_user_id()
    _thread = threading.Thread(target=asyncio.run, args=(thread_function(user_id),))
    _thread.start()


@on_command("sync_now", block=True).handle()
@check_session_handler
async def sync_now(bot: Bot, event: Event):
    if 'group' in event.get_event_name():
        await bot_send(bot, event, MSG_PRIVATE)
        return

    user_id = event.get_user_id()
    update_s3si_ts()
    u = get_or_set_user(user_id=user_id)
    if not (u and u.session_token and u.api_key):
        msg = 'Please set api_key first, /set_api_key'
        if isinstance(bot, QQBot):
            msg = '请先设置 api_key, /set_api_key'
        await bot_send(bot, event, msg)
        return

    msg = get_post_stat_msg(user_id)
    if not msg:
        msg = 'All done!'
    await bot_send(bot, event, msg, parse_mode='Markdown')


@on_command("report", block=True).handle()
@check_session_handler
async def report(bot: Bot, event: Event):
    cmd_list = event.get_plaintext().strip().split(' ')
    report_day = ''
    if len(cmd_list) > 1:
        report_day = cmd_list[1].strip()
        try:
            dt.strptime(report_day, '%Y-%m-%d')
        except:
            msg = '日期格式错误，正确格式: /report 2023-07-01 或 /report'
            await bot_send(bot, event, message=msg, parse_mode='Markdown')
            return

    user_id = event.get_user_id()
    u = get_or_set_user(user_id=user_id)
    user_id = u.id
    msg = get_report(user_id=user_id, report_day=report_day)

    if not report_day:
        get_or_set_user(user_id=user_id, report_type=1)

    if msg and not report_day:
        msg += f'```\n\n早报订阅成功\n/unsubscribe 取消订阅```'
    elif not msg and not report_day:
        msg = f'```\n数据准备中。。。\n\n早报订阅成功\n/unsubscribe 取消订阅```'
    await bot_send(bot, event, message=msg, parse_mode='Markdown')


@on_command("unsubscribe", block=True).handle()
@check_session_handler
async def unsubscribe(bot: Bot, event: Event):
    get_or_set_user(user_id=event.get_user_id(), report_type=0)
    msg = f'```\n取消订阅成功\n/report 订阅早报```'
    await bot_send(bot, event, message=msg, parse_mode='Markdown')
