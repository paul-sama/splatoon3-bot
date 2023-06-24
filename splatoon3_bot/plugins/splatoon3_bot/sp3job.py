import os
import json
import subprocess
import asyncio
import threading

from collections import defaultdict
from datetime import datetime as dt
from nonebot import Bot, logger, get_driver
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.onebot.v11 import Bot as QQBot

from .db_sqlite import get_or_set_user, get_all_user
from .scripts.top_player import get_x_player


logger = logger.bind(cron=True)

async def cron_job(bot: Bot):
    """定时任务， 每分钟每个bot执行"""
    # logger.debug(f'cron_job {bot.self_id}')

    users = get_all_user()

    # check msg file every minute and send msg, can't send msg in thread
    await send_user_msg(bot, users)

    # 同步任务全在tg bot上执行，避免qq被风控下线无法同步
    if isinstance(bot, QQBot):
        return

    now = dt.now()

    # parse x rank player at 2:40
    if now.hour == 2 and now.minute == 40 and isinstance(bot, TGBot):
        get_x_player()

    # run every 3 hours
    if not (now.hour % 3 == 0 and now.minute == 0):
        return

    update_s3si_ts()

    for u in users:
        if not u.api_key or not u.session_token:
            continue
        # if (isinstance(bot, TGBot) and not u.user_id_tg) or (isinstance(bot, QQBot) and not u.user_id_qq):
        #     continue

        _thread = threading.Thread(target=asyncio.run, args=(thread_function(u.id),))
        _thread.start()


async def send_user_msg(bot, users):
    path_folder = f'{os.path.abspath(os.path.join(__file__, os.pardir))}/resource'
    for u in users:
        if not u.api_key or not u.session_token:
            continue
        if (isinstance(bot, TGBot) and not u.user_id_tg) or (isinstance(bot, QQBot) and not u.user_id_qq):
            continue
        file_msg_path = os.path.join(path_folder, f'msg_{u.id}.txt')
        if not os.path.exists(file_msg_path):
            continue
        # logger.debug(f"get msg file: {file_msg_path}")
        msg = ''
        with open(file_msg_path, 'r') as f:
            msg = f.read()
        if msg:
            try:
                ret = None
                if isinstance(bot, TGBot):
                    ret = await bot.send_message(chat_id=u.user_id_tg, text=msg, disable_web_page_preview=True)
                elif isinstance(bot, QQBot):
                    ret = await bot.send_private_msg(user_id=u.user_id_qq, message=msg)
                if ret:
                    logger.debug(f"{u.id} send message: {ret}")
                    logger.debug(f"{u.id} delete message file: {file_msg_path}")
                    logger.info(msg)
                    os.remove(file_msg_path)
            except Exception as e:
                logger.error(f"{u.id}, post_battle_to_stat_ink: {e}, {msg}")


async def thread_function(user_id):
    u = get_or_set_user(user_id=user_id)
    logger.debug(f"get user: {u.username}, have api_key: {u.api_key}")

    path_folder = f'{os.path.abspath(os.path.join(__file__, os.pardir))}/resource'

    msg = get_post_stat_msg(u.id)
    if msg:
        logger.debug(f'{u.id}, {u.username}, {msg}')
        file_msg_path = os.path.join(path_folder, f'msg_{u.id}.txt')
        with open(file_msg_path, 'w') as f:
            f.write(msg)


def update_s3si_ts():
    dir_plugin = os.path.abspath(os.path.join(__file__, os.pardir))
    path_folder = f'{dir_plugin}/resource'
    if not os.path.exists(path_folder):
        os.mkdir(path_folder)
    os.chdir(path_folder)

    # get s3s code
    s3s_folder = f'{path_folder}/s3sits_git'
    if not os.path.exists(s3s_folder):
        cmd = f'git clone https://github.com/spacemeowx2/s3si.ts {s3s_folder}'
        rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
        logger.debug(f'cli: {rtn}')
        os.chdir(s3s_folder)
    else:
        os.chdir(s3s_folder)
        os.system('git restore .')
        cmd = f'git pull'
        rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
        logger.debug(f'cli: {rtn}')

    # edit agent
    cmd_list = [
        """sed -i "1,5s/s3si.ts/s3si.ts - t.me\/splatoon3_bot/g" ./src/constant.ts""",
    ]
    for cmd in cmd_list:
        logger.debug(f'cli: {cmd}')
        os.system(cmd)

    dir_user_configs = f'{s3s_folder}/user_configs'
    if not os.path.exists(dir_user_configs):
        os.mkdir(dir_user_configs)


def exported_to_stat_ink(user_id, session_token, api_key, user_lang):
    logger.debug(f'exported_to_stat_ink: {user_id}')
    logger.debug(f'session_token: {session_token}')
    logger.debug(f'api_key: {api_key}')
    user_lang = user_lang or 'zh-CN'

    dir_plugin = os.path.abspath(os.path.join(__file__, os.pardir))
    s3sits_folder = f'{dir_plugin}/resource/s3sits_git'
    os.chdir(s3sits_folder)

    path_config_file = f'{s3sits_folder}/user_configs/config_{user_id}.json'
    if not os.path.exists(path_config_file):
        config_data = {
            "userLang": user_lang,
            "loginState": {
                "sessionToken": session_token
            },
            "statInkApiKey": api_key
        }
        with open(path_config_file, 'w') as f:
            f.write(json.dumps(config_data, indent=2, sort_keys=False, separators=(',', ': ')))
    else:
        for cmd in (
                f"""sed -i 's/userLang[^,]*,/userLang\": \"{user_lang}\",/g' {path_config_file}""",
                f"""sed -i 's/sessionToken[^,]*,/sessionToken\": \"{session_token}\",/g' {path_config_file}""",
                f"""sed -i 's/statInkApiKey[^,]*,/statInkApiKey\": \"{api_key}\",/g' {path_config_file}""",
        ):
            logger.debug(f'cli: {cmd}')
            os.system(cmd)

    configs = get_driver().config
    deno_path = getattr(configs, 'deno_path', None)
    if not deno_path or not os.path.exists(deno_path):
        logger.info(f'deno_path not set: {deno_path or ""} '.center(120, '-'))
        return

    cmd = f'{deno_path} run -Ar ./s3si.ts -n -p {path_config_file}'
    logger.debug(cmd)
    rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
    logger.debug(f'{user_id} cli: {rtn}')

    battle_cnt = 0
    coop_cnt = 0
    url = ''
    for line in rtn.split('\n'):
        line = line.strip()
        if not line:
            continue
        if 'exported to https://stat.ink' in line:
            if 'salmon3' in line:
                coop_cnt += 1
            else:
                battle_cnt += 1
            url = line.split('to ')[1].split('spl3')[0].split('salmon3')[0][:-1]

    logger.debug(f'{user_id} result: {battle_cnt}, {coop_cnt}, {url}')
    if battle_cnt or coop_cnt:
        return battle_cnt, coop_cnt, url


def get_post_stat_msg(user_id):
    u = get_or_set_user(user_id=user_id)
    logger.debug(f"get user: {u.username}, have api_key: {u.api_key}")
    if not (u and u.session_token and u.api_key):
        return

    res = exported_to_stat_ink(u.id, u.session_token, u.api_key, u.acc_loc)
    if not res:
        return

    battle_cnt, coop_cnt, url = res
    msg = 'Exported'
    if battle_cnt:
        msg += f' {battle_cnt} battles'
    if coop_cnt:
        msg += f' {coop_cnt} jobs'

    if battle_cnt and not coop_cnt:
        url += '/spl3'
    elif coop_cnt and not battle_cnt:
        url += '/salmon3'
    msg += f' to\n{url}'

    logger.debug(f'{u.id}, {u.username}, {msg}')

    db_user_info = defaultdict(str)
    if u.user_info:
        db_user_info = json.loads(u.user_info)
    db_user_info['url_stat_ink'] = url.replace('/spl3', '').replace('/salmon3', '')
    get_or_set_user(user_id=u.id, user_info=json.dumps(db_user_info))
    return msg
