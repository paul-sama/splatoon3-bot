import asyncio
import json
import threading

from nonebot import logger, on_startswith, on_command, get_driver, get_bots

from nonebot.message import event_preprocessor
from nonebot.permission import SUPERUSER

from .config import plugin_config
from .db_sqlite import set_db_info, clean_db_cache
from .scripts.report import update_user_info_first, update_user_info
from .sp3msg import MSG_HELP, MSG_HELP_QQ, MSG_HELP_CN
from .sp3job import cron_job, sync_stat_ink
from .utils import bot_send, notify_tg_channel, get_event_info, Kook_Bot, Tg_Bot, V11_Bot, V12_Bot, QQ_Bot

from .cmd_get import *
from .cmd_push import *
from .cmd_set import *
from .cmd_broadcast import *
from .bot_comment import *


@on_startswith(("/", "、"), priority=1, block=False).handle()
async def all_command(bot: Bot, event: Event):
    data = {'user_id': event.get_user_id()}
    data.update(await get_event_info(bot, event))
    set_db_info(**data)


@on_startswith(("/", "、"), priority=99).handle()
async def unknown_command(bot: Bot, event: Event):
    logger.info(f'unknown_command {event.get_event_name()}')
    if 'private' in event.get_event_name():
        _msg = "Sorry, I didn't understand that command. /help"
        if isinstance(bot, (QQ_Bot, V12_Bot, Kook_Bot)):
            _msg = '无效命令，输入 /help 查看帮助'
        await bot.send(event, message=_msg)


@on_command("help", aliases={'h', '帮助', '说明', '文档'}, priority=10).handle()
async def _help(bot: Bot, event: Event):
    # 帮助菜单日程插件优先模式
    if plugin_config.splatoon3_schedule_plugin_priority_mode:
        return
    else:
        if isinstance(bot, Tg_Bot):
            await bot_send(bot, event, message=MSG_HELP, disable_web_page_preview=True)
        elif isinstance(bot, QQ_Bot):
            msg = MSG_HELP_QQ
            await bot_send(bot, event, message=msg)
        elif isinstance(bot, (V12_Bot, Kook_Bot,)):
            msg = MSG_HELP_CN
            await bot_send(bot, event, message=msg)


@get_driver().on_startup
async def bot_on_start():
    version = utils.BOT_VERSION
    logger.info(f' bot start, version: {version} '.center(120, '-'))
    await notify_tg_channel(f'bot start, version: {version}')


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
    if isinstance(bot, QQ_Bot):
        bot_type = 'QQ'
    elif isinstance(bot, V12_Bot):
        bot_type = 'WeChat'
    elif isinstance(bot, Kook_Bot):
        bot_type = 'Kook'

    logger.info(f' {bot_type} bot connect {bot.self_id} '.center(60, '-').center(120, ' '))

    job_id = f'sp3_cron_job_{bot.self_id}'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f'remove job {job_id} first')

    # 选择每个平台对应发信bot
    if ((isinstance(bot, Tg_Bot)) and (bot.self_id == plugin_config.splatoon3_notify_tg_bot_id)) or (
            (isinstance(bot, Kook_Bot)) and (bot.self_id == plugin_config.splatoon3_notify_kk_bot_id)):
        scheduler.add_job(
            cron_job, 'interval', minutes=1, id=job_id, args=[bot],
            misfire_grace_time=59, coalesce=True, max_instances=1
        )
        logger.info(f'add job {job_id}')

    if bot_type == 'QQ':
        text = f'bot {bot_type}: {bot.self_id} online ~'
        if plugin_config.splatoon3_bot_disconnect_notify:
            await notify_tg_channel(text)


@get_driver().on_bot_disconnect
async def _(bot: Bot):
    bot_type = 'Telegram'
    if isinstance(bot, QQ_Bot):
        bot_type = 'QQ'
    elif isinstance(bot, V12_Bot):
        bot_type = 'WeChat'
    elif isinstance(bot, Kook_Bot):
        bot_type = 'Kook'

    text = f'bot {bot_type}: {bot.self_id} disconnect !!!!!!!!!!!!!!!!!!!'
    if plugin_config.splatoon3_bot_disconnect_notify:
        try:
            await notify_tg_channel(text)
        except Exception as e:
            logger.warning(f"{text}")
            logger.warning(f"日志通知失败: {e}")


@event_preprocessor
async def tg_private_msg(bot: Tg_Bot, event: Event):
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
        try:
            await notify_tg_channel(text)
        except Exception as e:
            logger.warning("text")
            logger.warning(f"日志通知失败: {e}")


@event_preprocessor
async def kk_private_msg(bot: Kook_Bot, event: Event):
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
        await bot_send(bot, event, message=f'get_event_top end')

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
        if key in ('push',):
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

    elif plain_text == 'update_user_info_first':
        await bot_send(bot, event, message="即将开始update_user_info_first", parse_mode='Markdown')
        threading.Thread(target=asyncio.run, args=(update_user_info_first(),)).start()

    elif plain_text == 'update_user_info':
        await bot_send(bot, event, message="即将开始整理并发送日报", parse_mode='Markdown')
        threading.Thread(target=asyncio.run, args=(update_user_info(),)).start()

    elif plain_text == 'sync_stat_ink':
        from .db_sqlite import get_all_user
        users = get_all_user()
        await bot_send(bot, event, message="即将开始sync_stat_ink", parse_mode='Markdown')

        u_id_lst = [u.id for u in users if u.session_token and u.api_key]

        if not u_id_lst:
            return

        threading.Thread(target=sync_stat_ink, args=(u_id_lst,)).start()

    elif plain_text == 'md_test':
        md = """#### 传说 400 210% +310(310p) 
| | | |  |
| -- | --: |--|--|
|W1 | 41/26(58) |∼ 雾|  |
|W2 | 36/28(63) |≈ | <img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/252059408283fbcb69ca9c18b98effd3b8653ab73b7349c42472281e5a1c38f9_0.png?Expires=1704844800&Signature=YFflfVhdvdOmyBrrnY-ZMslRZR2pbdWugnoXUIKC9Bw310VWvuPTZhmlYCGmB0eNIRH3zeyTe~5hh-Lv0IaV8v8aNjYO8t5PVGJofc8N6IOql9Nf-iHsN9CICi1cO-nNIelaeuqImbw5Ghb78pWRnXdpHnZ8h3~Y1CrbkS3eyaHtoKd5oe~nPR1QDEzGOHgcR7nlcyGAAO8Ef5YBJOQ33g7cl1nj~bUGDXoFO3Snkc-08tWdug6MYeDlzzdRmlGaPeQK4pnDm89uxm~rNf07~klXLR5ivW4ggI31KKidznB9kX1xBCV36oOVbDcOzhSEsH-UAeFJpc-x1Sqe76i-lg__&Key-Pair-Id=KNBS2THMRC385"/> |
|W3 | 22/30(54) |≈ | <img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/380e541b5bc5e49d77ff1a616f1343aeba01d500fee36aaddf8f09d74bd3d3bc_0.png?Expires=1704844800&Signature=cupCB4JOrwBppJjRfVv4Cw~ZG2~j7wl9XXoozfnMOPIFFC5PFPAoyd97LZQildbumqRVvqfeOXgov39h6ZSw8SklSj-tDwiHQX3aJvGqyCvfGu4D6P53TQ5KjMFw3Y6~GpPzq~CxsIJ5KhTprbaQVEHXkVKxg3~wbnzvvpYe6tL~73f3oRAoebD~-8AdcURFJ~BqA74eidj9Ii5vMzW1py-UeuyupsL0r28pjnSyxIe8sodl5sfyTTYQH5gEomyaoUfKBWQEhRDxfXSXKikd~K-VNj7n3fYxrw~3dBK-AbvWraaMJX0gX7J2o8gMzBSYyIIXhdiwO8MRzhXRfFAXNA__&Key-Pair-Id=KNBS2THMRC385"/><img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/380e541b5bc5e49d77ff1a616f1343aeba01d500fee36aaddf8f09d74bd3d3bc_0.png?Expires=1704844800&Signature=cupCB4JOrwBppJjRfVv4Cw~ZG2~j7wl9XXoozfnMOPIFFC5PFPAoyd97LZQildbumqRVvqfeOXgov39h6ZSw8SklSj-tDwiHQX3aJvGqyCvfGu4D6P53TQ5KjMFw3Y6~GpPzq~CxsIJ5KhTprbaQVEHXkVKxg3~wbnzvvpYe6tL~73f3oRAoebD~-8AdcURFJ~BqA74eidj9Ii5vMzW1py-UeuyupsL0r28pjnSyxIe8sodl5sfyTTYQH5gEomyaoUfKBWQEhRDxfXSXKikd~K-VNj7n3fYxrw~3dBK-AbvWraaMJX0gX7J2o8gMzBSYyIIXhdiwO8MRzhXRfFAXNA__&Key-Pair-Id=KNBS2THMRC385"/><img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/680379f8b83e5f9e033b828360827bc2f0e08c34df1abcc23de3d059fe2ac435_0.png?Expires=1704844800&Signature=RJ~woXyFZ5jBZ72AxG8UMBfayZd3j-egucLG9Cr~hpVk7cG3TtndsGMsmohaR~LLgKBXlmcoiRZc9xswbaH41y0imntmlvL69k8Czoc0hZkI-CcS~kxyPZjd36HlJbco2u0djOFuB9-KWYoNlYiWjBXQNd6IOW9-AjBsTZ4quRKhRRr8SFAZYNEqBbJHaPwcRj-VbbCU8~Q9168GhFSKJVylQ~6MzTdOHD1HLWV28e25375~ic42WuFmX3oA0y3lQzZyDd3Zcy2FUp9KUeYf2AzTkOXzcJnx~LyoARE0rcCJ4nx3avRRjKYEhW3Z~CwILMVPVlycbDK5dFQJl2Wi6w__&Key-Pair-Id=KNBS2THMRC385"/><img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/680379f8b83e5f9e033b828360827bc2f0e08c34df1abcc23de3d059fe2ac435_0.png?Expires=1704844800&Signature=RJ~woXyFZ5jBZ72AxG8UMBfayZd3j-egucLG9Cr~hpVk7cG3TtndsGMsmohaR~LLgKBXlmcoiRZc9xswbaH41y0imntmlvL69k8Czoc0hZkI-CcS~kxyPZjd36HlJbco2u0djOFuB9-KWYoNlYiWjBXQNd6IOW9-AjBsTZ4quRKhRRr8SFAZYNEqBbJHaPwcRj-VbbCU8~Q9168GhFSKJVylQ~6MzTdOHD1HLWV28e25375~ic42WuFmX3oA0y3lQzZyDd3Zcy2FUp9KUeYf2AzTkOXzcJnx~LyoARE0rcCJ4nx3avRRjKYEhW3Z~CwILMVPVlycbDK5dFQJl2Wi6w__&Key-Pair-Id=KNBS2THMRC385"/><img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/252059408283fbcb69ca9c18b98effd3b8653ab73b7349c42472281e5a1c38f9_0.png?Expires=1704844800&Signature=YFflfVhdvdOmyBrrnY-ZMslRZR2pbdWugnoXUIKC9Bw310VWvuPTZhmlYCGmB0eNIRH3zeyTe~5hh-Lv0IaV8v8aNjYO8t5PVGJofc8N6IOql9Nf-iHsN9CICi1cO-nNIelaeuqImbw5Ghb78pWRnXdpHnZ8h3~Y1CrbkS3eyaHtoKd5oe~nPR1QDEzGOHgcR7nlcyGAAO8Ef5YBJOQ33g7cl1nj~bUGDXoFO3Snkc-08tWdug6MYeDlzzdRmlGaPeQK4pnDm89uxm~rNf07~klXLR5ivW4ggI31KKidznB9kX1xBCV36oOVbDcOzhSEsH-UAeFJpc-x1Sqe76i-lg__&Key-Pair-Id=KNBS2THMRC385"/><img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/bd327d1b64372dedefd32adb28bea62a5b6152d93aada5d9fc4f669a1955d6d4_0.png?Expires=1704844800&Signature=i11ShrPx~UmGVB~4rh~NxV-IZK0cCRcnfRT2L38yj0K8Qk2tD~e0bd8AF3m1BBGkg-iM~jEwn5tdylvLbwC37iHM--17061UEHDZwQGiKWF1phEP8TFy-f3OsEEq8XLyBe1XLCfp3-aMlSON8za77~I6wcR2RinP2qzgc~GOOW4zYmEbqs-fxDkJjWedDyEiPg8q-1CtaomjCueXxWABzyJ-lbJSvNPHOgnzavyxCcLYmfhs6Vw0SxzIqPf36UPDXbXKJemHNWi-2pMM0RLTnbwaM0-Qf~erXLrhez-HtyYzI~Jzq56AnduA4coHiA0x7LcNoaIevmMwu5-UoTmXGQ__&Key-Pair-Id=KNBS2THMRC385"/><img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/bd327d1b64372dedefd32adb28bea62a5b6152d93aada5d9fc4f669a1955d6d4_0.png?Expires=1704844800&Signature=i11ShrPx~UmGVB~4rh~NxV-IZK0cCRcnfRT2L38yj0K8Qk2tD~e0bd8AF3m1BBGkg-iM~jEwn5tdylvLbwC37iHM--17061UEHDZwQGiKWF1phEP8TFy-f3OsEEq8XLyBe1XLCfp3-aMlSON8za77~I6wcR2RinP2qzgc~GOOW4zYmEbqs-fxDkJjWedDyEiPg8q-1CtaomjCueXxWABzyJ-lbJSvNPHOgnzavyxCcLYmfhs6Vw0SxzIqPf36UPDXbXKJemHNWi-2pMM0RLTnbwaM0-Qf~erXLrhez-HtyYzI~Jzq56AnduA4coHiA0x7LcNoaIevmMwu5-UoTmXGQ__&Key-Pair-Id=KNBS2THMRC385"/> |


#### 99 (99)
|  |   ||  |||||
| --: |--:|--:|--:|--|--|--|--|
|x13| 33 |3d |472 |1r| <img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_skin_img/42c1cbf34f1b4a6d0db238fcdba614a32b068ae351810c533df7e6a33c8c64d8_0.png?Expires=1704844800&Signature=BVi1hWYbDIISLMNIa8nZ0vPeZhYZdKO3dXJEuEjdXJ8wgXx-mjunq-xe6Wta9wcFnS7785FLv2H0kYA7YiDWaQcN0fLCVEC1tKM6NhRtShCx6Z7M0Lp-ge51mY~7cru~ESIlo1W9nsNucDGEUmgBqSZSDdre~S2CDAVFx6QLwEXtjc4eKNbOnW-RMhXbkCZxrQTQzXQTCeEkPx8rc9kaFatNFYLdtxmqgNdNdKq~zqtfOjAPY-MBuPINRBE1Kja7b7zdQ6XEwgY2IvQweFdndm2nyvLHSU3Y-HVUf1KYGEuddaxIS7YTJrxU2hT8~Lf1AIPKEYrsbrUD50ZV3Mc5UA__&Key-Pair-Id=KNBS2THMRC385"/> keo|<img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/680379f8b83e5f9e033b828360827bc2f0e08c34df1abcc23de3d059fe2ac435_0.png?Expires=1704844800&Signature=RJ~woXyFZ5jBZ72AxG8UMBfayZd3j-egucLG9Cr~hpVk7cG3TtndsGMsmohaR~LLgKBXlmcoiRZc9xswbaH41y0imntmlvL69k8Czoc0hZkI-CcS~kxyPZjd36HlJbco2u0djOFuB9-KWYoNlYiWjBXQNd6IOW9-AjBsTZ4quRKhRRr8SFAZYNEqBbJHaPwcRj-VbbCU8~Q9168GhFSKJVylQ~6MzTdOHD1HLWV28e25375~ic42WuFmX3oA0y3lQzZyDd3Zcy2FUp9KUeYf2AzTkOXzcJnx~LyoARE0rcCJ4nx3avRRjKYEhW3Z~CwILMVPVlycbDK5dFQJl2Wi6w__&Key-Pair-Id=KNBS2THMRC385'/> |<img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/e3874d7d504acf89488ad7f68d29a348caea1a41cd43bd9a272069b0c0466570_0.png?Expires=1704844800&Signature=A42hdTiOjCe6PyDeG3E9KaK1pySTjAgqkhmDzZXn32rQf1HvP1mTICBZF8wDgYce2IyS5lMjfyvuh-QJX787~oyDA7HUbY6F2GaFDstcoF~cczIGQufrURtEXUBtP4t58fiTvOp~UwQpd1kaHpjBd4rtnyucbHMW45rSdSnwWOdoRce64qH7MLyqIARbtx5P4sW7bpUAFUdKhQ0Hh-AJDiCcTHmpI8GV0yz1ss72-QNNRCk0CBWsIgVXPkryh1vE-~dSS0uUT3lrorQ-C3dIJ-DGkhAcVbvYPAuxxsMFG~KLBCJUucpS51GOgYLS8de3lbfJXOsEjyt3WDIPxoq5-g__&Key-Pair-Id=KNBS2THMRC385'/><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/f3dbd98d5b0e89f7be7eff25a5c63a06045fe64d8ffd5886e79c855e16791563_0.png?Expires=1704844800&Signature=fdPnQSLDA3c-LEmhFzfV351u2F~AhSJ0kmQz3Rv64t9R44siFG7yzXQKaWaKhy7I-iRGPqWzoisBoEd0Z3ZtqIMhKC9yhVx3GbCUxk70HnvyMzTmBCnFEGjYKZtH5LKiCb87v5UMWYHfD~3QIf4p0sf0cgZJjtHv2PgcsjEzMKhy1QEVLu9NdpFAgzJr87x8BsYeGkENrifUR2M24erC9f7~gU4CnFST0SZekOugQpDUw8arwoguP72Y0L~n32Z1eSGoONPb7rKI9yxCn57Z1NAuOTXzTtE8ho3OWI6-11a4UJA3trhU5pCgZ34oERUMLc5ttKZDSBGKYnxWYNQOtw__&Key-Pair-Id=KNBS2THMRC385'/><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/0d2963b386b6da598b8da1087eab3f48b99256e2e6a20fc8bbe53b34579fb338_0.png?Expires=1704844800&Signature=tF-49Mpolf9yoHy5VfbkCogSpyAdgv83B2gwWeXLY5ssGKhuPvZxcNyfxMj5F4EA2OBQRYMQoEXdLCCXlQ0DqBR0FjA7eteIhY1QkppRdF5-z-Y5GwYD2jhkxGHqnW9uTWAueQCfrNJw26DR4xor1SB1b0B4Ka5cwNW~reCKb-VCkOLHtZNBodxBg57~12qtmqx4GBSjJA5W7VEJqnVWpTQw0-PiLPAwpDtLK~NXvp0-17D~jbYbqQ9a2BxXfjKiIqJIfIwt3JfHMR1FEDTBp9Dx4dSHpqw8GIdHDtdY4T6baTlmxfjnB7xc6XBU8gQQISO92V1F5WPbOfe1h-jmVA__&Key-Pair-Id=KNBS2THMRC385'/>|
|x8| 20 |3d |567 |1r| <img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_skin_img/42c1cbf34f1b4a6d0db238fcdba614a32b068ae351810c533df7e6a33c8c64d8_0.png?Expires=1704844800&Signature=BVi1hWYbDIISLMNIa8nZ0vPeZhYZdKO3dXJEuEjdXJ8wgXx-mjunq-xe6Wta9wcFnS7785FLv2H0kYA7YiDWaQcN0fLCVEC1tKM6NhRtShCx6Z7M0Lp-ge51mY~7cru~ESIlo1W9nsNucDGEUmgBqSZSDdre~S2CDAVFx6QLwEXtjc4eKNbOnW-RMhXbkCZxrQTQzXQTCeEkPx8rc9kaFatNFYLdtxmqgNdNdKq~zqtfOjAPY-MBuPINRBE1Kja7b7zdQ6XEwgY2IvQweFdndm2nyvLHSU3Y-HVUf1KYGEuddaxIS7YTJrxU2hT8~Lf1AIPKEYrsbrUD50ZV3Mc5UA__&Key-Pair-Id=KNBS2THMRC385"/> <span style="color:skyblue">しょくえん <img height='36px' style='position:absolute;right:5px;margin-top:-6px' src='https://cdn-image-e0d67c509fb203858ebcb2fe3f88c2aa.baas.nintendo.com/1/ca30f3d912a2c01c'/></span>|<img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/380e541b5bc5e49d77ff1a616f1343aeba01d500fee36aaddf8f09d74bd3d3bc_0.png?Expires=1704844800&Signature=cupCB4JOrwBppJjRfVv4Cw~ZG2~j7wl9XXoozfnMOPIFFC5PFPAoyd97LZQildbumqRVvqfeOXgov39h6ZSw8SklSj-tDwiHQX3aJvGqyCvfGu4D6P53TQ5KjMFw3Y6~GpPzq~CxsIJ5KhTprbaQVEHXkVKxg3~wbnzvvpYe6tL~73f3oRAoebD~-8AdcURFJ~BqA74eidj9Ii5vMzW1py-UeuyupsL0r28pjnSyxIe8sodl5sfyTTYQH5gEomyaoUfKBWQEhRDxfXSXKikd~K-VNj7n3fYxrw~3dBK-AbvWraaMJX0gX7J2o8gMzBSYyIIXhdiwO8MRzhXRfFAXNA__&Key-Pair-Id=KNBS2THMRC385'/> |<img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/0d2963b386b6da598b8da1087eab3f48b99256e2e6a20fc8bbe53b34579fb338_0.png?Expires=1704844800&Signature=tF-49Mpolf9yoHy5VfbkCogSpyAdgv83B2gwWeXLY5ssGKhuPvZxcNyfxMj5F4EA2OBQRYMQoEXdLCCXlQ0DqBR0FjA7eteIhY1QkppRdF5-z-Y5GwYD2jhkxGHqnW9uTWAueQCfrNJw26DR4xor1SB1b0B4Ka5cwNW~reCKb-VCkOLHtZNBodxBg57~12qtmqx4GBSjJA5W7VEJqnVWpTQw0-PiLPAwpDtLK~NXvp0-17D~jbYbqQ9a2BxXfjKiIqJIfIwt3JfHMR1FEDTBp9Dx4dSHpqw8GIdHDtdY4T6baTlmxfjnB7xc6XBU8gQQISO92V1F5WPbOfe1h-jmVA__&Key-Pair-Id=KNBS2THMRC385'/><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/e3874d7d504acf89488ad7f68d29a348caea1a41cd43bd9a272069b0c0466570_0.png?Expires=1704844800&Signature=A42hdTiOjCe6PyDeG3E9KaK1pySTjAgqkhmDzZXn32rQf1HvP1mTICBZF8wDgYce2IyS5lMjfyvuh-QJX787~oyDA7HUbY6F2GaFDstcoF~cczIGQufrURtEXUBtP4t58fiTvOp~UwQpd1kaHpjBd4rtnyucbHMW45rSdSnwWOdoRce64qH7MLyqIARbtx5P4sW7bpUAFUdKhQ0Hh-AJDiCcTHmpI8GV0yz1ss72-QNNRCk0CBWsIgVXPkryh1vE-~dSS0uUT3lrorQ-C3dIJ-DGkhAcVbvYPAuxxsMFG~KLBCJUucpS51GOgYLS8de3lbfJXOsEjyt3WDIPxoq5-g__&Key-Pair-Id=KNBS2THMRC385'/><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/082489b182fbbabddde40831dac5867d6acc4778b6a38d8f5c8d445455d638eb_0.png?Expires=1704844800&Signature=Fe8KiS-5U5tUJL3FonxHY62Ig8dvGrf~rNWjV~sa03blJx86O0~QSJjjNvg8BI3kLulmqBLvnuOQBR3~DhDyz71SIMwIR2X9kb0mHR9ie-69jBL5S3Uf2YEMWDOZUcYIL3yVOxnHscENRkZhZLHCNQcSz6RjbhDabzLvnAv3enm0-URuwR5RDMXSHc9MZk-EIXMzxr8awnDrVMcj9Vlo6iPrNoUvOo9z9DDq-S~CYaZomx3bQRJ6Su0SDpQ~rnXOVwAQDHMjIJP6IZ9nRhno1aYGiZSayeSXu2hUm5yD9J3qPdo37eA18uvrXFtJ34Fg5s-7LjUomIrhtHIPFujNiA__&Key-Pair-Id=KNBS2THMRC385'/>|
|x17| 21 |3d |1075 |2r| <img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_skin_img/89df74f2b5fbc49f76fb31f730fed012bb77f903746e81df108958010c95ef53_0.png?Expires=1704844800&Signature=tJVpDZX3Sx5UMM21WL2h-PmeUXMZTsKUvXqQOO3t3c5oASX2g1J-aZERiJhapL7-iU6LuFT4szmTqQTrS6nytf0TjhpVxyTy86-yYSy1ys92xn8RsKJjJRHr7OFwKsWfonelq1mWmoUI6Kf6M4gXvZCDXkNAiP4ZZ2s2q23Pm8ZdTlAjGr7j6icWoDk~qj4LynDPF35yBkNNZAM9Xu62KM7fW~ugJf1kfa34PXZ9-Hp-F1XSfW4Jcbutf1T4UdeAJfvYCdbWqLrrey9-bz8jGfe4ga3TPPkbgpV0dUucGk7RMniGvWxNnQ2AME7U6aFiGQmF39iT7fM4whPFhNR9eQ__&Key-Pair-Id=KNBS2THMRC385"/> キラークイーン|<img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/252059408283fbcb69ca9c18b98effd3b8653ab73b7349c42472281e5a1c38f9_0.png?Expires=1704844800&Signature=YFflfVhdvdOmyBrrnY-ZMslRZR2pbdWugnoXUIKC9Bw310VWvuPTZhmlYCGmB0eNIRH3zeyTe~5hh-Lv0IaV8v8aNjYO8t5PVGJofc8N6IOql9Nf-iHsN9CICi1cO-nNIelaeuqImbw5Ghb78pWRnXdpHnZ8h3~Y1CrbkS3eyaHtoKd5oe~nPR1QDEzGOHgcR7nlcyGAAO8Ef5YBJOQ33g7cl1nj~bUGDXoFO3Snkc-08tWdug6MYeDlzzdRmlGaPeQK4pnDm89uxm~rNf07~klXLR5ivW4ggI31KKidznB9kX1xBCV36oOVbDcOzhSEsH-UAeFJpc-x1Sqe76i-lg__&Key-Pair-Id=KNBS2THMRC385'/> |<img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/082489b182fbbabddde40831dac5867d6acc4778b6a38d8f5c8d445455d638eb_0.png?Expires=1704844800&Signature=Fe8KiS-5U5tUJL3FonxHY62Ig8dvGrf~rNWjV~sa03blJx86O0~QSJjjNvg8BI3kLulmqBLvnuOQBR3~DhDyz71SIMwIR2X9kb0mHR9ie-69jBL5S3Uf2YEMWDOZUcYIL3yVOxnHscENRkZhZLHCNQcSz6RjbhDabzLvnAv3enm0-URuwR5RDMXSHc9MZk-EIXMzxr8awnDrVMcj9Vlo6iPrNoUvOo9z9DDq-S~CYaZomx3bQRJ6Su0SDpQ~rnXOVwAQDHMjIJP6IZ9nRhno1aYGiZSayeSXu2hUm5yD9J3qPdo37eA18uvrXFtJ34Fg5s-7LjUomIrhtHIPFujNiA__&Key-Pair-Id=KNBS2THMRC385'/><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/0d2963b386b6da598b8da1087eab3f48b99256e2e6a20fc8bbe53b34579fb338_0.png?Expires=1704844800&Signature=tF-49Mpolf9yoHy5VfbkCogSpyAdgv83B2gwWeXLY5ssGKhuPvZxcNyfxMj5F4EA2OBQRYMQoEXdLCCXlQ0DqBR0FjA7eteIhY1QkppRdF5-z-Y5GwYD2jhkxGHqnW9uTWAueQCfrNJw26DR4xor1SB1b0B4Ka5cwNW~reCKb-VCkOLHtZNBodxBg57~12qtmqx4GBSjJA5W7VEJqnVWpTQw0-PiLPAwpDtLK~NXvp0-17D~jbYbqQ9a2BxXfjKiIqJIfIwt3JfHMR1FEDTBp9Dx4dSHpqw8GIdHDtdY4T6baTlmxfjnB7xc6XBU8gQQISO92V1F5WPbOfe1h-jmVA__&Key-Pair-Id=KNBS2THMRC385'/><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/f3dbd98d5b0e89f7be7eff25a5c63a06045fe64d8ffd5886e79c855e16791563_0.png?Expires=1704844800&Signature=fdPnQSLDA3c-LEmhFzfV351u2F~AhSJ0kmQz3Rv64t9R44siFG7yzXQKaWaKhy7I-iRGPqWzoisBoEd0Z3ZtqIMhKC9yhVx3GbCUxk70HnvyMzTmBCnFEGjYKZtH5LKiCb87v5UMWYHfD~3QIf4p0sf0cgZJjtHv2PgcsjEzMKhy1QEVLu9NdpFAgzJr87x8BsYeGkENrifUR2M24erC9f7~gU4CnFST0SZekOugQpDUw8arwoguP72Y0L~n32Z1eSGoONPb7rKI9yxCn57Z1NAuOTXzTtE8ho3OWI6-11a4UJA3trhU5pCgZ34oERUMLc5ttKZDSBGKYnxWYNQOtw__&Key-Pair-Id=KNBS2THMRC385'/>|
|x14| 25 |1d |1128 |6r| <img height="18" src="https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_skin_img/06ecf4c72d76108a734cd545150fb7af9bfde7e38244c205392224217a66b730_0.png?Expires=1704844800&Signature=gCsmmIutbmyUfQwDNrdHNTFZKJHSoNRiMpUKPz6Br8J-2cDYRpLl9hU-qi2HgjfOqTOzt52kKCXOTRLiiO8AZ26EnDel1TgqfRrmbPUMEpLmkBx074BxEV732WZ5E~0Tt7yZlhafCHoOU04I33piowbHZCiPhWfXP6MwQDTpFLAdd94a0XUbQTZkcXrCGB9VR-Szlk6punKnBtU0nfotYKBeR3kKpqy9siEpVsDR4HxW7aI2RWEBI-p6G5uFPlEbrDojtVLQndxXW0kuNKQiJ2e0sZaK195WakaNnTI3NBO0SvPlw2raBkxGtP~-YxWT3xUgFJWv5n6XIIoSCGAUiw__&Key-Pair-Id=KNBS2THMRC385"/> <span style="color:skyblue">Z <img height='36px' style='position:absolute;right:5px;margin-top:-6px' src='https://cdn-image-e0d67c509fb203858ebcb2fe3f88c2aa.baas.nintendo.com/1/445af94c4f815025'/></span>|<img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/special_img/blue/bd327d1b64372dedefd32adb28bea62a5b6152d93aada5d9fc4f669a1955d6d4_0.png?Expires=1704844800&Signature=i11ShrPx~UmGVB~4rh~NxV-IZK0cCRcnfRT2L38yj0K8Qk2tD~e0bd8AF3m1BBGkg-iM~jEwn5tdylvLbwC37iHM--17061UEHDZwQGiKWF1phEP8TFy-f3OsEEq8XLyBe1XLCfp3-aMlSON8za77~I6wcR2RinP2qzgc~GOOW4zYmEbqs-fxDkJjWedDyEiPg8q-1CtaomjCueXxWABzyJ-lbJSvNPHOgnzavyxCcLYmfhs6Vw0SxzIqPf36UPDXbXKJemHNWi-2pMM0RLTnbwaM0-Qf~erXLrhez-HtyYzI~Jzq56AnduA4coHiA0x7LcNoaIevmMwu5-UoTmXGQ__&Key-Pair-Id=KNBS2THMRC385'/> |<img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/f3dbd98d5b0e89f7be7eff25a5c63a06045fe64d8ffd5886e79c855e16791563_0.png?Expires=1704844800&Signature=fdPnQSLDA3c-LEmhFzfV351u2F~AhSJ0kmQz3Rv64t9R44siFG7yzXQKaWaKhy7I-iRGPqWzoisBoEd0Z3ZtqIMhKC9yhVx3GbCUxk70HnvyMzTmBCnFEGjYKZtH5LKiCb87v5UMWYHfD~3QIf4p0sf0cgZJjtHv2PgcsjEzMKhy1QEVLu9NdpFAgzJr87x8BsYeGkENrifUR2M24erC9f7~gU4CnFST0SZekOugQpDUw8arwoguP72Y0L~n32Z1eSGoONPb7rKI9yxCn57Z1NAuOTXzTtE8ho3OWI6-11a4UJA3trhU5pCgZ34oERUMLc5ttKZDSBGKYnxWYNQOtw__&Key-Pair-Id=KNBS2THMRC385'/><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/082489b182fbbabddde40831dac5867d6acc4778b6a38d8f5c8d445455d638eb_0.png?Expires=1704844800&Signature=Fe8KiS-5U5tUJL3FonxHY62Ig8dvGrf~rNWjV~sa03blJx86O0~QSJjjNvg8BI3kLulmqBLvnuOQBR3~DhDyz71SIMwIR2X9kb0mHR9ie-69jBL5S3Uf2YEMWDOZUcYIL3yVOxnHscENRkZhZLHCNQcSz6RjbhDabzLvnAv3enm0-URuwR5RDMXSHc9MZk-EIXMzxr8awnDrVMcj9Vlo6iPrNoUvOo9z9DDq-S~CYaZomx3bQRJ6Su0SDpQ~rnXOVwAQDHMjIJP6IZ9nRhno1aYGiZSayeSXu2hUm5yD9J3qPdo37eA18uvrXFtJ34Fg5s-7LjUomIrhtHIPFujNiA__&Key-Pair-Id=KNBS2THMRC385'/><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/weapon_illust/e3874d7d504acf89488ad7f68d29a348caea1a41cd43bd9a272069b0c0466570_0.png?Expires=1704844800&Signature=A42hdTiOjCe6PyDeG3E9KaK1pySTjAgqkhmDzZXn32rQf1HvP1mTICBZF8wDgYce2IyS5lMjfyvuh-QJX787~oyDA7HUbY6F2GaFDstcoF~cczIGQufrURtEXUBtP4t58fiTvOp~UwQpd1kaHpjBd4rtnyucbHMW45rSdSnwWOdoRce64qH7MLyqIARbtx5P4sW7bpUAFUdKhQ0Hh-AJDiCcTHmpI8GV0yz1ss72-QNNRCk0CBWsIgVXPkryh1vE-~dSS0uUT3lrorQ-C3dIJ-DGkhAcVbvYPAuxxsMFG~KLBCJUucpS51GOgYLS8de3lbfJXOsEjyt3WDIPxoq5-g__&Key-Pair-Id=KNBS2THMRC385'/>|

|        | ||
|-------|--:|--|
|<span style="color: green">3</span> |<span style="color: green">3</span> | <span style="color: green"><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/f59fe344bd941f90dc8d3458ffd29b6586c1cffd00864967e7766a5a931dc4f6_0.png?Expires=1704844800&Signature=SnHiMEUDxaXmZ1ZLP~ZJHN~I-Y36-fTxBgNlz4zt2y81J25Yijdo~XVfbJpocBApw-HihA40l0Yl1bG65hV4IKBVrT~9a6utABwz9VQn1674vZUw68SYmZBzPQfUbKF6bgcQ-JGEo9~1jWiks7~8Mn~TvMf7-dHw1C~FZAkBrBt0l93dZn-55DSlR7FhrwzmgSX5DgPlMz4Ls2lcxSJgAOTbCxIop0Dbmxf~vpUdozoRdXPPyQDLQrAUwzHxpONe7CW-3d~7FtnCMMBXw4kXuB9nKDt1rAKVsIEaBk4Uh2a6~7kDZbfVMv6aU~ir4XkfBaF3yG1uywEBFqlvYpJ0~Q__&Key-Pair-Id=KNBS2THMRC385'/> 炸弹鱼</span>|
|4(1) |7 | <img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/03c31763738c5628db6d8e7dd3ba0fd2fcb79a1f47694488b51969375148edde_0.png?Expires=1704844800&Signature=V-XQzb7moTDsVTI3zTE8DYcK-RMphzBbhNfRLKeGG2gVHkrSZRt8ViuHwUTYsnVCDzikq52UR8lVkLolu0Y-2dgH4DDqofYGYcPTi9UgS~UpfKf7MtzlANzqHSKvmRi5iGyOhFgi9J0wOmFCyPzcz0J8dqATURkb4b~KRc~6zPQWauVOhw8sctNgQWJQ74OB2i~JgiTf8I4rOJgFYrth~LiI1BSbNTPGKbAUgbf3PcS1BPSRFCgAeAJpzYWEGpo1UMs-tWDIn-faggTyHyDis~hkE5z4WsL41XsaUsE0V1GUiN175Oi4ejPcfhxlDJLpqR124qyC7F-8T2q-yQ~HLQ__&Key-Pair-Id=KNBS2THMRC385'/> 垫肩飞鱼|
|<span style="color: green">6(2)</span> |<span style="color: green">6</span> | <span style="color: green"><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/3a3e2c87b96b92e31ffc59a273b7d6aca20f9941e05ad84d6ae26092a627aa34_0.png?Expires=1704844800&Signature=D5zoJhHF3wCnR9-vAyJNwUPJY87gJExt-T8yVH9i13eKUUwoHWXPBl6OAIPlyxQmkyeVfCxtLqS97ILN0DKie8Ayw67Wl8x-023AoCumYqPY0fEOC1AWModjaNw3tlbTkvkH1hVqWexO9t6EgDKglMLS9wF6mQvzjZdFM3V~x4LlrYtItS9de7HrkvztJ~k~98ujy2bwscSOpte~EH1byZ-6kIqRrsD~EwfPzcN3cF9KLspECV7~5TonG34BsDRdcYx~~aOd8SxSWOMg12HQB7JbuGlSVk~QSy8yyVO9vdnujqN5Ey2GO-R9TheQx1bq8uuZzRCQiB1gyNeWOkh82g__&Key-Pair-Id=KNBS2THMRC385'/> 铁板鱼</span>|
|<span style="color: green">6</span> |<span style="color: green">6</span> | <span style="color: green"><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/999097a0908a4560f05a16e3f97c07b5d10bed22bee6d2ce0eedb2e6a6dcb9d0_0.png?Expires=1704844800&Signature=uqWaVsdXHO9NkPowDP-GmJ9-qqTn~TLzkFrW3yrX5mAM72wp0IpBbo11YcB7aTptfDe1jrL-LyyJw26fX6Qegc5nIxM9~HpCm7Vhws7UaW6DyfqX7fs3pdxSUJ4-E6V-KQTZ54n3p-FujW9kr-NN2~~pHV6MCSCeP9Xz4Otdmj76rcsDPm0NN1LypOTnYkaIlAOfMcMEdNKAXlJvMa5IpZ0RhaNLdjCHMDVkfcltRm~0SVNib4Tt3vS-K25WmSd~1Y41~gRtlCtenNAft4KLGzMdKNis8HltxsOboDtJVZjOu3UfXWg72JPeQaNv9Uc3BuOA8ltGs0US9ke2jvzjAA__&Key-Pair-Id=KNBS2THMRC385'/> 蛇鱼</span>|
|7(1) |8 | <img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/2d740da6f03364c3c289625455374f734fd8a96b25c26fde13912e90f3aea68c_0.png?Expires=1704844800&Signature=qoB4qvFKMjNEKOVVF0bnfJbDY5WMEkGPVS3pLqWwRFgVTh8JBNNdvwueIUXsxO7Ddis-NKlH2uyhb6kXgAyO03fHm6prHoBUoxwrIKqaFc0dgyxe-VjjdjMMZz697Zkzxe2Tz06KTKCdOb4mEU-Y1h618n6MYbqXQ6633iY5vCzKzlEkS9VCvW2a-WwM8pc3BK1fvgPLEUKVozokcTs0YhI2bwC~kClPwNve-AeT8cfz5LE-ERjUzhhAvO1sDtS67D-c7lxFh1IUdIfd~-VyE-kIxF9gi-F9k2OMoy8ar-DNrTYs~W~EN8ZhUJhLeAlqxainLwyEjMP0d97tUnl-~w__&Key-Pair-Id=KNBS2THMRC385'/> 高塔鱼|
|<span style="color: green">4(1)</span> |<span style="color: green">4</span> | <span style="color: green"><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/fd5abb7a9087c528e45a7a4e29c9c03d673b69d6f0ba2f424f6df8b732d9919a_0.png?Expires=1704844800&Signature=Bi0mVeK1Jpwiy6d0Tzblo99He6ChXgUSG1GVv0vHr1suCpx0boFnubb9EvzAsrIPb9oHR7c7tymP9R0jFQ6sr15o3EnmlSXh9cRk1Mmo6Y9eVadh6FkF~G8e273YMl307noeu0CiiccH1cEYWL4qLQnrqkBf4MXFSjrttbeEOU7-4JBFB6RpuW0tWHL0Zb3jOQHDOZsrr0X15QPbUoqXpzNL3wGH8sZrU2nU8wcr5OP1zlZ8Pz6CI6XngwW6Jp-3cpjGdCWzTe6ybL5VfBhep~JKiTrFsMzSsP2FbtoOSfdWwGh~eW8f8upxnwFiqrB4WNwNvDiHFtnmCXHtiXnjNw__&Key-Pair-Id=KNBS2THMRC385'/> 鼹鼠鱼</span>|
|2(1) |4 | <img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/faed7977b2144ac5979de0ca7d23aefd507e517c3fbe19431054ac5a6ba300fa_0.png?Expires=1704844800&Signature=GCkSTJgackm90PytB2tOu0BXsJOS0JYWtLt170ksQ0REXlzkh4HBTIs7gVhepVMHmMzbe1jzvawnsALAecy5xKR6F-slVA7WuZwpZks5up5m1QF5-CXSEGopQfqzWQg6q3B0PlNR7PPc4NLtn-I1B3jI3aFW7KejbeJf37bYavVNr2HJiVVv-aJSldBKmy6a5YpZXPkjWSPFqQzB-sZqIWE6mQ1ezNrCjGhUzXKuvG7w0IkoVdtJXJnvGrOj-CzlU1KbijuHgshJXXF1rUKkoxd-6bZq6Q9EyTXld7Ac~fG4ca43dHQcKbqoVx8fddfwBhOOELWL~JNkH6BR~HmHkw__&Key-Pair-Id=KNBS2THMRC385'/> 蝙蝠鱼|
|7(4) |8 | <img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/fb4851c75f62b8b50d9bac2128d6ef1c703c7884b63402762ddf78c1555e364a_0.png?Expires=1704844800&Signature=f-QIy3JfqgdtVyyKWvl9AI~lQZyjFWg8zucl-drTLf5V6ynFOGi7BnOYcC39HX2ZkRKBtm11xlruAcC5lKy7yEOYxmQ0XduP5jOswNIRAhZqbbqonV9bGoMkgQwjDD~Ny6caVM8wbeUp2zuEItuZ~feMzG0o8mYtLAHiyUQh0QUl6W5lU91npmF8fXUfWpcRds-I3CmDvWXjt1DM0opHxJCvnECD8o64F3msF6kAOnJXNjihIIpLg0AkGbdlrCzV0G1sw7eXc-kLbZkXTIq4k9H7pAPBG357mT8bevX7y5ToSv3UloOcMi2Is3d39VcoFOthWV65q2nSBDeFv6cdpg__&Key-Pair-Id=KNBS2THMRC385'/> 柱鱼|
|<span style="color: green">6(2)</span> |<span style="color: green">6</span> | <span style="color: green"><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/dbbf89da359fd880db49730ecc4f66150b148274aa005e22c1152cbf1a45e378_0.png?Expires=1704844800&Signature=rGu9ZkiHW-wb-wmbx-a44qcItjX5q3ptI1S0I~-lnTcfvuybzoENFJ9bmnwT~2jx7yk1qZ1AxfliqjCRBY5alJ7lVLIn0RtT1t1nufaUPKFDrrOFMkzwWXhisQR5eJsdPu~EO6muZNOYUbbI7w9iNg3XBL8oh~djfCLaQyoB7ZjrgU7CkNR3qzqnpS3jN~AZeiVRL36F56z~myhVK20P4axsVcPvboCxYqoKeQz43SvbKE6QqxUvxSwtxmvoZy1SL7QJ6xL84J7RTqdRFBkneHDuF8cMcifmMA5A5uSzlD9cXk-W3zD~tVdnY8vzjMfpb6RBWkx~O~CzmlnBdw-pKQ__&Key-Pair-Id=KNBS2THMRC385'/> 潜水鱼</span>|
|2 |6 | <img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/2c7a648b4c73f291b5ede9c55f33d4e3f99c263d3a27ef3d2eb2a96d328d66ac_0.png?Expires=1704844800&Signature=O~L3aq9U4HHwRn1EV7I542Ug1e2cAKhMNxQrVEUO02sLuvo~NI3D4WolnILmtj130VFSwkjrJiSsSVeb9YZKhI5pwDED78IVqXv9222Uceb2MQvpUcdpTL-hNGTdsQi3aCtZ2YRcepGnJ4o0V07k52W0WYpjC~GC5zj4nTUca6HcFj0UZuxoajvLs78qtjWWRnGzdwirUI6tI~vBs3CYe3ZqAmHg44hZb7wp9~iGjPK6dce4c2KeuYenihe5Mwnt7zwRkVwcGBsPEqYinI0neNj99VSIbjjb0d7rZuad90PTn7fq4clNCEfXv4ABJ19p6balL20f2oPnunNtGdrgEg__&Key-Pair-Id=KNBS2THMRC385'/> 铁球鱼|
|<span style="color: green">4(1)</span> |<span style="color: green">4</span> | <span style="color: green"><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/2185696079cc39328cd69f0570e219f09b61d4a56508260fe97b16347ae8a55f_0.png?Expires=1704844800&Signature=l-1qgWVnLNa8aE-gW~xg6soX6~UbhYzUIusbTC8FRa01Egxnt7GKe9D2xc7CB8X6oKYhKBGzWYrinOriRDDZqelczBWqFMp958xP8T~WmDCVeJSpL9YBtd8kX-xNeM1CLF5iLWXcW3xF6v6SjiS7TornlW8uzAIwma6djBn0yy7KLBO-sOMoOTB69gY26OOIC2s~3BNV-WoyGu0qwHSmuL9cEAzLRF9gXQBDL9~SGKvYS9g0pT9FhRcFUSn2RujAzIRJvtkeOuke31QrI9bpMYFVAh8W1Anma--W~Q7fLXDKp~cOsLKY0R6C3vZAhuM8aVzrzDqx95iX~MnenpQQNQ__&Key-Pair-Id=KNBS2THMRC385'/> 锅盖鱼</span>|
|<span style="color: green">4</span> |<span style="color: green">4</span> | <span style="color: green"><img height='18' src='https://api.lp1.av5ja.srv.nintendo.net/resources/prod/v2/coop_enemy_img/a35aa2982499e9a404fdb81f72fbaf553bc47f7682cc67f9b8c32ca9910e2cbf_0.png?Expires=1704844800&Signature=nFjSA-QojFw~~s7OEyXB~pwW-ofidjEv-5V~PdDO2WVoQ3y1u5AcDg2lZpxA73oUXT6IoVdrKJgxuJJV1~eH31lQbDqxPuuX2V-tw-vHDplJhLNR7S9wUn2NszjGq0OfdP0JYOz0DeXxstBb88l-boNfEz2ENAcJHW2xzgbJfR~SYqcWh7Rh7-DEbUcHM3S1SlA5AVyxxxpQVTlzQBZ0gPc0Rx-Wj1dqb5UEKw9Qgm1Cfkw~UZmkxHh7fDXjh2aW-wjLmvHmQLYAeQs3X9P8uFJ1aeabis7lSQeujMeaw0VXTfYT8WYs~2m3UfjeiwH1lrEtgPeGRc-T1qOlfHzo3g__&Key-Pair-Id=KNBS2THMRC385'/> 金鲑鱼</span>|
"""

        await bot_send(bot, event, message=md, parse_mode='Markdown')

    elif plain_text == 'thread_count':
        thread_num = len(threading.enumerate())
        await bot_send(bot, event, message=f'当前线程数量为{str(thread_num)}', parse_mode='Markdown')

    elif plain_text == 'clean_db_cache':
        clean_db_cache()
        await bot_send(bot, event, message="数据库缓存已清空", parse_mode='Markdown')