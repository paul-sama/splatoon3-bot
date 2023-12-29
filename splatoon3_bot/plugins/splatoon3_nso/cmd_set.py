import os
import base64
import json
import secrets
from collections import defaultdict
from datetime import datetime as dt

from nonebot import on_command, logger, get_driver, on_startswith, on_regex
from nonebot.adapters import Event, Bot
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Depends
from nonebot.typing import T_State

from .config import plugin_config
from .db_sqlite import set_db_info, get_user, get_or_set_user, get_all_user
from .sp3iksm import log_in, login_2, A_VERSION
from .splat import Splatoon
from .sp3bot import get_last_battle_or_coop
from .sp3job import get_post_stat_msg, update_s3si_ts, sync_stat_ink_func, threading, asyncio
from .utils import bot_send, _check_session_handler, Kook_Bot, QQ_Bot, Tg_Bot, V11_Bot, V12_Bot, Tg_File, QQ_GME, \
    notify_tg_channel, GLOBAL_LOGIN_STATUS_DICT, get_event_info
from .scripts.report import get_report

__all__ = ['login', 'login_id', 'clear_db_info', 'set_db_info', 'get_set_battle_info']
MSG_PRIVATE = '请私信机器人完成登录操作'

matcher_login = on_command("login", priority=10, block=True)


@matcher_login.handle()
async def login(bot: Bot, event: Event, matcher: Matcher, state: T_State):
    if isinstance(bot, QQ_Bot):
        kk_guild_id = plugin_config.splatoon3_kk_guild_id
        msg = f"Q群当前无法登录nso，请至其他平台完成登录后获取绑定码\nKook服务器id：{kk_guild_id}"
        await bot_send(bot, event, msg)
        await matcher.finish()
        return

    if 'group' in event.get_event_name():
        if isinstance(bot, (V12_Bot, Kook_Bot, QQ_Bot)):
            await matcher_login.finish(MSG_PRIVATE)
            return
        await matcher_login.finish(MSG_PRIVATE, reply_message=True)
        await matcher.finish()
        return

    user_id = event.get_user_id()
    u = get_or_set_user(user_id=user_id)
    if u and u.session_token:
        msg = '用户已经登录\n如需重新登录或切换账号请继续下面操作\n登出或清空账号数据 /clear_db_info'
        await bot_send(bot, event, msg)
        await matcher.finish()

    dir_path = os.path.dirname(os.path.abspath(__file__))
    img_path = f'{dir_path}/resource/sp3bot-login.gif'
    if isinstance(bot, Tg_Bot):
        try:
            logger.info(f'img_path: {img_path}')
            await bot.send(event, Tg_File.animation(img_path))
        except Exception as e:
            logger.error(f'login error: {e}')

    url, auth_code_verifier = log_in(A_VERSION)
    GLOBAL_LOGIN_STATUS_DICT.update(
        {user_id: {"auth_code_verifier": auth_code_verifier, "create_time": dt.now().strftime("%Y-%m-%d %H:%M:%S")}})
    logger.info(f'get login url: {url}')
    logger.info(f'auth_code_verifier: {auth_code_verifier}')
    if url:
        msg = ''
        if isinstance(bot, Tg_Bot):
            msg = f'''
Navigate to this URL in your browser:
{url}
Log in, right click the "Select this account" button, copy the link address, and paste below. (Valid for 2 minutes)
            '''
        elif isinstance(bot, (V11_Bot, V12_Bot, Kook_Bot)):
            msg = f'''在浏览器中打开下面链接（移动端复制链接至其他浏览器）,
登陆后，右键账号后面的红色按钮 (手机端长按复制)
复制链接后发送给机器人 (两分钟内有效！)
'''
        if msg:
            await bot.send(event, message=msg)
            await bot.send(event, message='我是分割线'.center(120, '-'))
            await bot.send(event, message=url)


@on_startswith("npf", priority=10).handle()
async def login_id(bot: Bot, event: Event, state: T_State):
    text = event.get_plaintext()
    user_id = event.get_user_id()
    # 查找用户登录字典
    user_login_info = GLOBAL_LOGIN_STATUS_DICT.get(user_id)
    if user_login_info is None:
        return

    auth_code_verifier = user_login_info.get("auth_code_verifier")

    err_msg = '登录失败，请 /login 重试, 复制新链接'
    if (not text) or (len(text) < 500) or (not text.startswith('npf')) or (auth_code_verifier is None):
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

    event_info = await get_event_info(bot, event)
    user_name = event_info.get('username')
    id_type = 'qq'
    if isinstance(bot, Tg_Bot):
        id_type = 'tg'
    if isinstance(bot, V12_Bot):
        id_type = 'wx'
    if isinstance(bot, Kook_Bot):
        id_type = 'kk'
    data = {
        'session_token': session_token,
        'user_id': user_id,
        'id_type': id_type,
    }
    if isinstance(bot, (Tg_Bot, Kook_Bot)):
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
    if isinstance(bot, (V11_Bot, V12_Bot, Kook_Bot)):
        msg = f"""登录成功！机器人现在可以从App获取你的数据。
如果希望在q群使用nso查询，请发送
/get_login_code
获取一次性跨平台绑定码

常用指令:
/me - 显示你的信息
/friends - 显示在线的喷喷好友
/last - 显示最近一场对战或打工
/report - 获取昨天或指定日期的日报数据
/start_push - 开启推送模式
/set_api_key - 设置 api_key, 同步数据到 https://stat.ink
更多完整nso操作指令:
https://docs.qq.com/sheet/DUkZHRWtCUkR0d2Nr?tab=BB08J2
"""
    await bot.send(event, message=msg)
    GLOBAL_LOGIN_STATUS_DICT.pop(user_id)

    logger.info(f'login success:{user_name} {user_id}')
    user = get_user(user_id=user_id)
    _splt = Splatoon(user.id, user.session_token)
    await _splt.set_gtoken_and_bullettoken()

    res_battle = await _splt.get_recent_battles(skip_check_token=True)
    b_info = res_battle['data']['latestBattleHistories']['historyGroups']['nodes'][0]['historyDetails']['nodes'][0]
    player_code = base64.b64decode(b_info['player']['id']).decode('utf-8').split(':')[-1][2:]
    set_db_info(user_id=user_id, id_type=data['id_type'], user_id_sp=player_code)
    _msg = f'new_login_user: 会话昵称:{user_name}\nns_player_code:{player_code}\n{session_token}'
    await notify_tg_channel(_msg)


@on_command("clear_db_info", priority=10, block=True).handle(parameterless=[Depends(_check_session_handler)])
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
        api_key=None,
        acc_loc=None,
        user_info=None,
    )

    msg = "All your data cleared! 已清空账号数据!"
    logger.info(msg)
    await bot_send(bot, event, message=msg)


@on_command("get_login_code", priority=10, block=True).handle(parameterless=[Depends(_check_session_handler)])
async def get_login_code(bot: Bot, event: Event):
    if isinstance(bot, QQ_Bot):
        await bot_send(bot, event, '暂不支持')
        return
    if 'group' in event.get_event_name():
        await bot_send(bot, event, '请私信机器人')
        return

    user_id = event.get_user_id()
    _code = secrets.token_urlsafe(20)
    # 生成一次性 code
    get_or_set_user(user_id=user_id, user_id_bind=_code)
    msg = f'请在Q群内艾特机器人并发送下行指令完成跨平台绑定\n该绑定码为一次性的随机字符串，不用担心别人重复使用\n\n/set_login {_code}'
    await bot_send(bot, event, message=msg)


@on_command("set_login", priority=10, block=True).handle()
async def func_set_login(bot: QQ_Bot, event: Event):
    if isinstance(bot, Kook_Bot):
        await bot_send(bot, event, '暂不支持')
        return

    _code = event.get_plaintext().strip()[10:].strip()
    user_id = event.get_user_id()
    all_user = get_all_user()

    u = ''
    for user in all_user:
        if user.user_id_bind == _code:
            u = user
            break

    if not u:
        await bot_send(bot, event, 'code错误，账号绑定失败')
        return

    # 清空 code
    get_or_set_user(user_id=u.id, user_id_bind='')

    # 复制 session_token
    get_or_set_user(user_id=user_id, session_token=u.session_token)

    msg = f"""登录成功！机器人现在可以从App获取你的数据。
/me - 显示你的信息
/friends - 显示在线的喷喷好友
/last - 显示最近一场对战或打工
/report - 喷喷早报
"""
    await bot_send(bot, event, msg)

    logger.info(f'login success: {user_id}\n{msg}')
    user = get_user(user_id=user_id)
    _splt = Splatoon(user.id, user.session_token)
    await _splt.set_gtoken_and_bullettoken()

    res_battle = await _splt.get_recent_battles(skip_check_token=True)
    b_info = res_battle['data']['latestBattleHistories']['historyGroups']['nodes'][0]['historyDetails']['nodes'][0]
    player_code = base64.b64decode(b_info['player']['id']).decode('utf-8').split(':')[-1][2:]
    set_db_info(user_id=user_id, id_type='qq', user_id_sp=player_code)

    await notify_tg_channel(f'绑定QQ成功: {user_id}, {player_code}')


matcher_set_battle_info = on_command("set_battle_info", aliases={'sbi'}, priority=10, block=True)


@matcher_set_battle_info.handle(parameterless=[Depends(_check_session_handler)])
async def set_battle_info(bot: Bot, event: Event, matcher: matcher_set_battle_info):
    if isinstance(bot, QQ_Bot):
        await bot_send(bot, event, '暂不支持')
        return
    if 'group' in event.get_event_name():
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
    if isinstance(bot, (V11_Bot, V12_Bot, Kook_Bot)):
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


matcher_set_api_key = on_command("set_api_key", priority=10, block=True)


@matcher_set_api_key.handle(parameterless=[Depends(_check_session_handler)])
async def set_api_key(bot: Bot, event: Event, matcher: matcher_set_api_key):
    if isinstance(bot, QQ_Bot):
        await bot_send(bot, event, 'Q群不支持该命令，请从其他平台进行设置')
        return
    if 'group' in event.get_event_name():
        await matcher_set_battle_info.finish(MSG_PRIVATE)
        return

    msg = '''Please copy you api_key from https://stat.ink/profile then paste below'''
    if isinstance(bot, (V11_Bot, V12_Bot, Kook_Bot)):
        msg = '''请从 https://stat.ink/profile 页面复制你的 api_key 后发送给机器人
注册stat.ink账号后，无需其他操作，设置api_key
机器人会同步你的数据到 stat.ink (App最多保存最近50*5场对战和50场打工数据)
        '''
    await bot_send(bot, event, message=msg)


@on_regex("^[A-Za-z0-9_-]{30,}", priority=10, block=True).handle()
async def get_set_api_key(bot: Bot, event: Event):
    """stat api key匹配"""
    if 'group' in event.get_event_name():
        return
    api_key = event.get_plaintext().strip()
    if len(api_key) != 43:
        await matcher_set_api_key.finish("key错误,请重新复制key后发送给我")
        return

    user_id = event.get_user_id()
    logger.info(f'set_api_key: {api_key}')
    get_or_set_user(user_id=user_id, api_key=api_key)

    msg = f'''set_api_key success, bot will check every 2 hours and post your data to stat.ink.
first sync will be in minutes.
    '''
    if isinstance(bot, (V11_Bot, V12_Bot, Kook_Bot)):
        msg = f'''设置成功，机器人会检查一次并同步你的数据到 stat.ink
/api_notify 关 - 设置关闭推送通知
        '''
    await bot_send(bot, event, message=msg)

    update_s3si_ts()

    threading.Thread(target=sync_stat_ink_func, args=(user_id,)).start()


@on_command("sync_now", priority=10, block=True).handle(parameterless=[Depends(_check_session_handler)])
async def sync_now(bot: Bot, event: Event):
    if isinstance(bot, QQ_Bot):
        await bot_send(bot, event, '暂不支持')
        return
    if 'group' in event.get_event_name():
        await bot_send(bot, event, MSG_PRIVATE)
        return

    user_id = event.get_user_id()
    u = get_or_set_user(user_id=user_id)
    if not (u and u.session_token and u.api_key):
        msg = 'Please set api_key first, /set_api_key'
        if isinstance(bot, (V11_Bot, V12_Bot, Kook_Bot)):
            msg = '请先设置 api_key, /set_api_key'
        await bot_send(bot, event, msg)
        return

    update_s3si_ts()
    from .sp3job import sync_stat_ink
    u_id_lst = [user_id]
    threading.Thread(target=sync_stat_ink, args=(u_id_lst,)).start()
    msg = '''手动同步任务开始，请稍等~ '''
    await bot_send(bot, event, msg, parse_mode='Markdown')
    return


@on_command("api_notify", priority=10, block=True).handle(parameterless=[Depends(_check_session_handler)])
async def s_api_notify(bot: Bot, event: Event):
    if isinstance(bot, QQ_Bot):
        await bot_send(bot, event, '暂不支持')
        return
    if 'group' in event.get_event_name():
        await bot_send(bot, event, MSG_PRIVATE)
        return

    user_id = event.get_user_id()
    u = get_or_set_user(user_id=user_id)
    if not (u and u.session_token and u.api_key):
        msg = 'Please set api_key first, /set_api_key'
        if isinstance(bot, (V11_Bot, V12_Bot, Kook_Bot)):
            msg = '请先设置 api_key, /set_api_key'
        await bot_send(bot, event, msg)
        return

    cmd = event.get_plaintext().strip()
    api_notify = 1
    msg = '设置成功: '
    if '关' in cmd or '0' in cmd:
        api_notify = 0
        msg += '推送通知关，后台仍会继续同步数据到 stat.ink'
    else:
        msg += '推送通知开'

    get_or_set_user(user_id=user_id, api_notify=api_notify)
    await bot_send(bot, event, msg)


@on_command("report", priority=10, block=True).handle(parameterless=[Depends(_check_session_handler)])
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

    u = get_user(user_id=user_id)
    if not report_day:
        get_or_set_user(user_id=user_id, report_type=1)

    if isinstance(bot, QQ_Bot):
        # QQ要单独考虑提示文案
        if not msg and not report_day:
            msg = f'```\n数据准备中，请明天再查询\n```'
        elif not msg and report_day:
            msg = f'```\n没有查询到所指定日期的日报数据```'
    else:
        if msg and not report_day and not u.report_type:
            msg += f'```\n\n早报订阅成功\n/unsubscribe 取消订阅```'
        elif not msg and not report_day:
            msg = f'```\n数据准备中。。。\n\n早报订阅成功\n/unsubscribe 取消订阅```'
        elif not msg and report_day:
            msg = f'```\n数据准备中。。。```'

    await bot_send(bot, event, message=msg, parse_mode='Markdown')


@on_command("unsubscribe", block=True).handle(parameterless=[Depends(_check_session_handler)])
async def unsubscribe(bot: Bot, event: Event):
    if isinstance(bot, QQ_Bot):
        await bot_send(bot, event, '暂不支持')
        return
    get_or_set_user(user_id=event.get_user_id(), report_type=0)
    msg = f'```\n取消订阅成功\n/report 订阅早报```'
    await bot_send(bot, event, message=msg, parse_mode='Markdown')
