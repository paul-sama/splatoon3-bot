
import base64
import time
from nonebot import logger

from datetime import datetime as dt, timedelta

from ..splat import Splatoon
from ..db_sqlite import get_all_user, get_user, set_db_info, model_add_report

logger = logger.bind(report=True)


def set_user_info(user_id, skip_report=False):
    u = get_user(user_id=user_id)
    if not u or not u.session_token:
        return
    logger.debug(f'set_user_info: {user_id}, {u.user_id_qq or u.user_id_tg}, {u.username}')
    user_id = u.user_id_qq or u.user_id_tg or u.id
    splt = Splatoon(user_id, u.session_token)

    splt.test_page()
    time.sleep(1)
    splt.test_page()

    res_summary = splt.get_summary()
    history = res_summary['data']['playHistory']
    player = res_summary['data']['currentPlayer']
    first_play_time = history['gameStartTime']
    first_play_time = dt.strptime(first_play_time, '%Y-%m-%dT%H:%M:%SZ')
    nickname = player['name']

    # get last battle
    res_battle = splt.get_recent_battles(skip_check_token=True)
    b_info = res_battle['data']['latestBattleHistories']['historyGroups']['nodes'][0]['historyDetails']['nodes'][0]
    battle_t = base64.b64decode(b_info['id']).decode('utf-8').split('_')[0].split(':')[-1]
    player_code = base64.b64decode(b_info['player']['id']).decode('utf-8').split(':')[-1][2:]

    # get last coop
    res_coop = splt.get_coops()
    coop_id = res_coop['data']['coopResult']['historyGroups']['nodes'][0]['historyDetails']['nodes'][0]['id']
    coop_t = base64.b64decode(coop_id).decode('utf-8').split('_')[0].split(':')[-1]

    last_play_time = max(dt.strptime(battle_t, '%Y%m%dT%H%M%S'), dt.strptime(coop_t, '%Y%m%dT%H%M%S'))

    _dict = {
        'user_id': user_id,
        'id_type': 'qq' if u.user_id_qq else 'tg',
        'nickname': nickname,
        'user_id_sp': player_code,
        'first_play_time': first_play_time,
        'last_play_time': last_play_time,
    }
    logger.debug(f'set_user_info: {_dict}')
    set_db_info(**_dict)

    if last_play_time.date() == (dt.utcnow() - timedelta(days=1)).date() and skip_report is False:
        set_user_report(u, res_summary, res_coop, last_play_time, splt, player_code)


def set_user_report(u, res_summary, res_coop, last_play_time, splt, player_code):
    all_data = splt.get_all_res()

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
    model_add_report(**_report)


def update_user_info():
    t = dt.utcnow()
    users = get_all_user()
    for u in users:
        if not u or not u.session_token:
            continue

        try:
            set_user_info(u.id)
            # import threading
            # threading.Thread(target=set_user_info, args=(u.id,)).start()
        except Exception as e:
            logger.warning(e)
            logger.warning(f'update_user_info_failed: {u.id}, {u.user_id_qq or u.user_id_tg}, {u.username}')

    logger.info(f'update_user_info_end: {dt.utcnow() - t}')


def update_user_info_first():
    t = dt.utcnow()
    users = get_all_user()
    for u in users:
        if not u or not u.session_token:
            continue

        try:
            set_user_info(u.id, skip_report=True)
        except Exception as e:
            logger.warning(e)
            logger.warning(f'update_user_info_first_failed: {u.id}, {u.user_id_qq or u.user_id_tg}, {u.username}')

    logger.info(f'update_user_info_first_end: {dt.utcnow() - t}')
