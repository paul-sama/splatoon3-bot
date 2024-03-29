
import asyncio
import base64
import time
from nonebot import logger

from datetime import datetime as dt, timedelta

from ..splat import Splatoon
from ..db_sqlite import get_all_user, get_user, set_db_info, model_add_report, model_get_report
from ..utils import DIR_RESOURCE, os

cron_logger = logger.bind(cron=True)


async def set_user_info(user_id, skip_report=False, log=None):
    if log is not None:
        log = cron_logger
    else:
        log = logger
    try:
        u = get_user(user_id=user_id)
        if not u or not u.session_token:
            return

        log.debug(f'set_user_info: {user_id}, {u.user_id_qq or u.user_id_tg or u.user_id_wx or u.user_id_kk}, {u.username}')
        user_id = u.user_id_qq or u.user_id_tg or u.user_id_wx or u.user_id_kk or u.id
        splt = Splatoon(user_id, u.session_token)

        if skip_report:
            await splt.test_page()

        res_summary = await splt.get_summary()
        history = res_summary['data']['playHistory']
        player = res_summary['data']['currentPlayer']
        first_play_time = history['gameStartTime']
        first_play_time = dt.strptime(first_play_time, '%Y-%m-%dT%H:%M:%SZ')
        nickname = player['name']

        # get last battle
        res_battle = await splt.get_recent_battles(skip_check_token=True)
        b_info = res_battle['data']['latestBattleHistories']['historyGroups']['nodes'][0]['historyDetails']['nodes'][0]
        battle_t = base64.b64decode(b_info['id']).decode('utf-8').split('_')[0].split(':')[-1]
        player_code = base64.b64decode(b_info['player']['id']).decode('utf-8').split(':')[-1][2:]

        # get last coop
        res_coop = await splt.get_coops(skip_check_token=True)
        coop_id = res_coop['data']['coopResult']['historyGroups']['nodes'][0]['historyDetails']['nodes'][0]['id']
        coop_t = base64.b64decode(coop_id).decode('utf-8').split('_')[0].split(':')[-1]

        last_play_time = max(dt.strptime(battle_t, '%Y%m%dT%H%M%S'), dt.strptime(coop_t, '%Y%m%dT%H%M%S'))

        id_type = 'tg'
        if u.user_id_qq:
            id_type = 'qq'
        if u.user_id_wx:
            id_type = 'wx'
        if u.user_id_kk:
            id_type = 'kk'

        _dict = {
            'user_id': user_id,
            'id_type': id_type,
            'nickname': nickname,
            'user_id_sp': player_code,
            'first_play_time': first_play_time,
            'last_play_time': last_play_time,
            'gtoken': splt.gtoken,
            'bullettoken': splt.bullet_token,
        }
        log.debug(f'set_user_info: {_dict}')

        if skip_report:
            return _dict

        if last_play_time.date() >= (dt.utcnow() - timedelta(days=1)).date():
            _report = await set_user_report(u, res_summary, res_coop, last_play_time, splt, player_code)

            # tg, kk 才发早报
            _user_id = u.id if u.report_type and id_type in ('tg', 'kk') else ''

            return _dict, _report, _user_id

    except Exception as ex:
        log.warning(f'set_user_info error: {user_id}, {ex}')


async def set_user_report(u, res_summary, res_coop, last_play_time, splt, player_code):
    all_data = await splt.get_all_res(skip_check_token=True)

    history = res_summary['data']['playHistory']
    player = res_summary['data']['currentPlayer']
    nickname = player['name']

    total_cnt = all_data['data']['playHistory']['battleNumTotal']
    win_cnt = history['winCountTotal']
    lose_cnt = total_cnt - win_cnt
    win_rate = round(win_cnt / total_cnt * 100, 2)

    _l = history['leagueMatchPlayHistory']
    _ln = _l['attend'] - _l['gold'] - _l['silver'] - _l['bronze']
    _o = history['bankaraMatchOpenPlayHistory']
    _on = _o['attend'] - _o['gold'] - _o['silver'] - _o['bronze']

    ar = round((history.get('xMatchMaxAr') or {}).get('power') or 0, 2) or None
    lf = round((history.get('xMatchMaxLf') or {}).get('power') or 0, 2) or None
    gl = round((history.get('xMatchMaxGl') or {}).get('power') or 0, 2) or None
    cl = round((history.get('xMatchMaxCl') or {}).get('power') or 0, 2) or None
    max_power = max(ar or 0, lf or 0, gl or 0, cl or 0) or None

    coop = res_coop['data']['coopResult']
    card = coop['pointCard']
    p = coop['scale']

    _report = {
        'user_id': u.id,
        'user_id_sp': player_code,
        'nickname': nickname,
        'name_id': player['nameId'],
        'byname': player['byname'],
        'rank': history['rank'],
        'udemae': history['udemae'],
        'udemae_max': history['udemaeMax'],
        'total_cnt': total_cnt,
        'win_cnt': win_cnt,
        'lose_cnt': lose_cnt,
        'win_rate': win_rate,
        'paint': history['paintPointTotal'],
        'badges': len(history['badges']),
        'event_gold': _l['gold'],
        'event_silver': _l['silver'],
        'event_bronze': _l['bronze'],
        'event_none': _ln,
        'open_gold': _o['gold'],
        'open_silver': _o['silver'],
        'open_bronze': _o['bronze'],
        'open_none': _on,
        'max_power': max_power,
        'x_ar': ar,
        'x_lf': lf,
        'x_gl': gl,
        'x_cl': cl,
        'coop_cnt': card['playCount'],
        'coop_gold_egg': card['goldenDeliverCount'],
        'coop_egg': card['deliverCount'],
        'coop_boss_cnt': card['defeatBossCount'],
        'coop_rescue': card['rescueCount'],
        'coop_point': card['totalPoint'],
        'coop_gold': p['bronze'],
        'coop_silver': p['silver'],
        'coop_bronze': p['gold'],
        'last_play_time': last_play_time,
    }
    return _report


async def update_user_info():
    cron_logger.info(f'update_user_info start')
    t = dt.utcnow()

    users = [u for u in get_all_user() if u and u.session_token]
    users = sorted(users, key=lambda x: (-(x.report_type or 0), x.id))
    u = [u.id for u in users]

    path_folder = f'{DIR_RESOURCE}/user_msg'
    if not os.path.exists(path_folder):
        os.mkdir(path_folder)

    _pool = 20
    for i in range(0, len(u), _pool):
        _u_id_lst = u[i:i+_pool]
        tasks = [set_user_info(_id) for _id in _u_id_lst]
        res = await asyncio.gather(*tasks)
        for r in res:
            if not r:
                continue
            # 每次循环强制睡眠0.5s，使一分钟内最多触发120次发信，避免超出阈值
            time.sleep(0.5)
            try:
                _dict, _report, _uid = r
                if _dict:
                    set_db_info(**_dict)
                if _report:
                    model_add_report(**_report)
                if _uid:
                    msg = get_report(_uid)
                    if msg:
                        file_msg_path = os.path.join(path_folder, f'msg_{_uid}.txt')
                        with open(file_msg_path, 'a') as f:
                            f.write(msg)
            except Exception as ex:
                cron_logger.warning(f'update_user_info ex: {ex}')
                continue

    cron_logger.info(f'update_user_info_end: {dt.utcnow() - t}')


async def update_user_info_first():
    cron_logger.info(f'update_user_info_first start')
    t = dt.utcnow()
    users = [u for u in get_all_user() if u and u.session_token]
    users = sorted(users, key=lambda x: (-(x.report_type or 0), x.id))
    u = [u.id for u in users]

    _pool = 50
    for i in range(0, len(u), _pool):
        _u_id_lst = u[i:i+_pool]
        tasks = [set_user_info(_id, True) for _id in _u_id_lst]
        res = await asyncio.gather(*tasks)
        for r in res:
            if not r:
                continue
            set_db_info(**r)

    cron_logger.info(f'update_user_info_first end: {dt.utcnow() - t}')


def get_report(user_id, report_day=None):
    msg = '\n喷喷早报\n'
    if report_day:
        msg = '\n喷喷小报\n'
    u = get_user(user_id=user_id)
    report_list = model_get_report(user_id_sp=u.user_id_sp)

    # for r in report_list:
    #     logger.info(f'rrrrrrrrrrrr {r.id:>4}, {r.create_time}, {r.last_play_time}')

    if not report_list or len(report_list) == 1:
        return

    old = report_list[1]

    fst_day = ''
    if report_day:
        fst_day = report_list[-1].create_time.strftime('%Y-%m-%d')
        for r in report_list[1:]:
            if r.last_play_time.strftime('%Y-%m-%d') < max(report_day, fst_day):
                old = r
                break

    new = report_list[0]
    s_date = (old.create_time + timedelta(hours=8)).strftime('%Y%m%d')
    if report_day:
        s_date = max(report_day.replace('-', ''), s_date)
    e_date = (new.last_play_time + timedelta(hours=8)).strftime('%Y%m%d %H:%M')
    msg += f'统计区间HKT: {s_date[2:]} 08:00 ~ {e_date[2:]}\n\n'

    msg += f'{new.nickname}\n'
    for k in ('nickname', 'name_id', 'byname'):
        if getattr(old, k) != getattr(new, k):
            msg += f'{getattr(old, k)} -> {getattr(new, k)}\n'
    if old.rank != new.rank:
        msg += f'等级: {old.rank} -> {new.rank}\n'
    if old.udemae != new.udemae:
        msg += f'技术: {old.udemae} -> {new.udemae}\n'
    if old.udemae_max != new.udemae_max:
        msg += f'最高技术: {old.udemae_max} -> {new.udemae_max}\n'
    if old.total_cnt != new.total_cnt:
        rate_diff = round(new.win_rate - old.win_rate, 2)
        msg += f'总胜利数: (+{new.win_cnt - old.win_cnt}){new.win_cnt}/(+{new.total_cnt - old.total_cnt}){new.total_cnt} ({rate_diff:+}){new.win_rate/100:.2%}\n'
    if old.paint != new.paint:
        msg += f'涂墨面积: ({new.paint - old.paint:+}) {new.paint:,}p\n'
    if old.badges != new.badges:
        msg += f'徽章: (+{new.badges - old.badges}) {new.badges}\n'
    if (old.event_gold + old.event_silver + old.event_bronze + old.event_none) != (
            new.event_gold + new.event_silver + new.event_bronze + new.event_none):
        str_event = ''
        if old.event_gold != new.event_gold:
            str_event += f' 🏅️+{new.event_gold - old.event_gold}'
        if old.event_silver != new.event_silver:
            str_event += f' 🥈+{new.event_silver - old.event_silver}'
        if old.event_bronze != new.event_bronze:
            str_event += f' 🥉+{new.event_bronze - old.event_bronze}'
        if old.event_none != new.event_none:
            str_event += f' +{new.event_none - old.event_none}'
        msg += f'活动: {str_event}\n'
    if (old.open_gold + old.open_silver + old.open_bronze + old.open_none) != (
            new.open_gold + new.open_silver + new.open_bronze + new.open_none):
        str_open = ''
        if old.open_gold != new.open_gold:
            str_open += f' 🏅️+{new.open_gold - old.open_gold}'
        if old.open_silver != new.open_silver:
            str_open += f' 🥈+{new.open_silver - old.open_silver}'
        if old.open_bronze != new.open_bronze:
            str_open += f' 🥉+{new.open_bronze - old.open_bronze}'
        if old.open_none != new.open_none:
            str_open += f' +{new.open_none - old.open_none}'
        msg += f'开放: {str_open}\n'

    if old.coop_cnt != new.coop_cnt:
        msg += f'\n打工次数: (+{new.coop_cnt - old.coop_cnt}) {new.coop_cnt}\n'
    if old.coop_gold_egg != new.coop_gold_egg:
        msg += f'金鲑鱼卵: (+{new.coop_gold_egg - old.coop_gold_egg}) {new.coop_gold_egg}\n'
    if old.coop_egg != new.coop_egg:
        msg += f'鲑鱼卵: (+{new.coop_egg - old.coop_egg}) {new.coop_egg}\n'
    if old.coop_boss_cnt != new.coop_boss_cnt:
        msg += f'头目鲑鱼: (+{new.coop_boss_cnt - old.coop_boss_cnt}) {new.coop_boss_cnt}\n'
    if (old.coop_gold + old.coop_silver + old.coop_bronze) != (new.coop_gold + new.coop_silver + new.coop_bronze):
        str_coop = ''
        if old.coop_bronze != new.coop_bronze:
            str_coop += f' 🏅️{new.coop_bronze - old.coop_bronze:+}'
        if old.coop_silver != new.coop_silver:
            str_coop += f' 🥈{new.coop_silver - old.coop_silver:+}'
        if old.coop_gold != new.coop_gold:
            str_coop += f' 🥉{new.coop_gold - old.coop_gold:+}'
        msg += f'鳞片: {str_coop}\n'

    msg = f'```{msg}```'
    u = get_user(user_id=user_id)
    if report_day and fst_day and not u.report_type:
        msg += f'```\n\n订阅早报: /report```'
    logger.info(msg)
    return msg
