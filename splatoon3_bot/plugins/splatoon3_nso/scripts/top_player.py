
import base64
import json
import time
from datetime import datetime as dt
from nonebot import logger

from ..s3s import utils
from ..splat import Splatoon
from ..db_sqlite import (
    write_top_player, clean_top_player, get_all_user, write_top_all, clean_top_all, get_top_all_by_top_type
)

cron_logger = logger.bind(cron=True)

def parse_x_row(n, top_type, x_type, top_id):
    n = n['node']
    name = n['name']
    name_id = n['nameId']
    rank = n['rank']
    power = n['xPower']
    byname = n['byname']
    weapon = n['weapon']['name']
    p_id = base64.b64decode(n['id']).decode('utf-8')
    player_code = p_id.split('-')[-1]
    _top_type = f'{top_type}:{x_type}'
    weapon_id = int(base64.b64decode(n['weapon']['id']).decode('utf-8').split('-')[-1])

    row = [top_id, _top_type, rank, power, name, name_id, player_code, byname, weapon_id, weapon]
    # logger.info(row[:-1])
    write_top_player(row)
    row.append(dt.utcnow())
    write_top_all(row)


async def get_x_items(top_id, splt):
    """获取X排行榜第一屏数据"""
    _d = utils.gen_graphql_body('90932ee3357eadab30eb11e9d6b4fe52d6b35fde91b5c6fd92ba4d6159ea1cb7',
                                varname='id', varvalue=top_id)
    res = await splt._request(_d)
    return res


async def get_top_x(data_row, top_id, x_type, mode_hash, splt=None):
    logger.info(f'get_top_x: {top_id}, {x_type}')
    res = data_row
    if not res:
        return

    top_type = base64.b64decode(top_id).decode('utf-8')
    for n in res['data']['xRanking'][f'xRanking{x_type}']['edges']:
        parse_x_row(n, top_type, x_type, top_id)

    has_next_page = res['data']['xRanking'][f'xRanking{x_type}']['pageInfo']['hasNextPage']
    cursor = res['data']['xRanking'][f'xRanking{x_type}']['pageInfo']['endCursor']
    while True:
        if not has_next_page:
            break

        _d = {
            "extensions": {"persistedQuery": {"sha256Hash": mode_hash, "version": 1}},
            "variables": {'cursor': cursor, 'first': 25, 'page': 1, 'id': top_id}
        }
        _d = json.dumps(_d)
        _res = await splt._request(_d)
        for n in _res['data']['node'][f'xRanking{x_type}']['edges']:
            parse_x_row(n, top_type, x_type, top_id)

        cursor = _res['data']['node'][f'xRanking{x_type}']['pageInfo']['endCursor']
        has_next_page = _res['data']['node'][f'xRanking{x_type}']['pageInfo']['hasNextPage']
        logger.info(f'get page:  {cursor}, {has_next_page}')
        if not has_next_page:
            break

    for page in (2, 3, 4, 5):
        _d = {
            "extensions": {"persistedQuery": {"sha256Hash": mode_hash, "version": 1}},
            "variables": {'cursor': None, 'first': 25, 'page': page, 'id': top_id}
        }
        _d = json.dumps(_d)
        _res = await splt._request(_d)

        for n in _res['data']['node'][f'xRanking{x_type}']['edges']:
            parse_x_row(n, top_type, x_type, top_id)

        cursor = _res['data']['node'][f'xRanking{x_type}']['pageInfo']['endCursor']
        has_next_page = _res['data']['node'][f'xRanking{x_type}']['pageInfo']['hasNextPage']
        while True:
            if not has_next_page:
                break
            _d = {
                "extensions": {"persistedQuery": {"sha256Hash": mode_hash, "version": 1}},
                "variables": {'cursor': cursor, 'first': 25, 'page': page, 'id': top_id}
            }
            _d = json.dumps(_d)
            _res = await splt._request(_d)
            for n in _res['data']['node'][f'xRanking{x_type}']['edges']:
                parse_x_row(n, top_type, x_type, top_id)

            cursor = _res['data']['node'][f'xRanking{x_type}']['pageInfo']['endCursor']
            has_next_page = _res['data']['node'][f'xRanking{x_type}']['pageInfo']['hasNextPage']

            logger.info(f'get page:  {cursor}, {has_next_page}')
            if not has_next_page:
                break


async def parse_x_data(top_id, splt):
    clean_top_player(top_id)
    clean_top_all(top_id)
    first_rows = await get_x_items(top_id, splt)

    for _t in (
            ('Ar', '0dc7b908c6d7ad925157a7fa60915523dab4613e6902f8b3359ae96be1ba175f'),
            ('Lf', 'ca55206629f2c9fab38d74e49dda3c5452a83dd02a5a7612a2520a1fc77ae228'),
            ('Gl', '6ab0299d827378d2cae1e608d349168cd4db21dd11164c542d405ed689c9f622'),
            ('Cl', '485e5decc718feeccf6dffddfe572455198fdd373c639d68744ee81507df1a48')
    ):
        x_type, hash_mode = _t
        try:
            await get_top_x(first_rows, top_id, x_type, hash_mode, splt)
        except Exception as ex:
            logger.exception(f'get_top_x error: {top_id}, {x_type}, {ex}')
            continue
        time.sleep(5)


async def get_x_player():
    cron_logger.info(f'get_x_player start')
    s = time.time()

    users = get_all_user()
    splt = None
    for u in users:
        if u and u.session_token:
            user_id = u.user_id_qq or u.user_id_tg or u.id
            splt = Splatoon(user_id, u.session_token)
            break

    if not splt:
        cron_logger.info(f'no user login.')
        return

    # for top_id in ('WFJhbmtpbmdTZWFzb24tcDoy', 'WFJhbmtpbmdTZWFzb24tYToy'):  # season-2
    # for top_id in ('WFJhbmtpbmdTZWFzb24tcDoz', 'WFJhbmtpbmdTZWFzb24tYToz'):  #season-3
    # for top_id in ('WFJhbmtpbmdTZWFzb24tcDo0', 'WFJhbmtpbmdTZWFzb24tYTo0'):  #season-4
    # for top_id in ('WFJhbmtpbmdTZWFzb24tcDo1', 'WFJhbmtpbmdTZWFzb24tYTo1'):  #season-5
    for top_id in ('WFJhbmtpbmdTZWFzb24tcDo2', 'WFJhbmtpbmdTZWFzb24tYTo2'):  #season-6
        await parse_x_data(top_id, splt)

    cron_logger.info(f'get_x_player end. {time.time() - s}')


async def get_event_list(splt):
    data = utils.gen_graphql_body(utils.translate_rid['EventListQuery'])
    res = await splt._request(data)
    return res


async def get_event_items(splt, top_id):
    data = utils.gen_graphql_body(utils.translate_rid['EventBoardQuery'],
                                  varname='eventMatchRankingPeriodId', varvalue=top_id)
    res = await splt._request(data)
    return res


def parse_league(league):
    if not league:
        logger.info('no league')
        return

    play_time = league['data']['rankingPeriod']['endTime'].replace('T', ' ').replace('Z', '')
    play_time = dt.strptime(play_time, '%Y-%m-%d %H:%M:%S')
    league_name = league['data']['rankingPeriod']['leagueMatchSetting']['leagueMatchEvent']['name']
    logger.info(f'{play_time}, {league_name}')
    for team in league['data']['rankingPeriod']['teams']:
        top_id = team['id']
        logger.info(f'saving top_id: {top_id}')
        clean_top_all(top_id)
        top_type = base64.b64decode(top_id).decode('utf-8')
        for n in team['details']['nodes']:
            for player in n['players']:
                player_id = player['id']
                player_code = base64.b64decode(player_id).decode('utf-8').split(':')[-1][2:]
                weapon_id = int(base64.b64decode(player['weapon']['id']).decode('utf-8').split('-')[-1])
                weapon = player['weapon']['name']
                db_row = [top_id, top_type, n['rank'], n['power'], player['name'], player['nameId'], player_code,
                          player['byname'], weapon_id, weapon, play_time]
                write_top_all(db_row)


async def task_get_league_player(splt):
    logger.info(f'get_league_player start')
    res = await get_event_list(splt)
    if not res:
        return
    edges = res['data']['leagueMatchRankingSeasons']['edges']
    for n in edges[::-1]:
        in_ed = n['node']['leagueMatchRankingTimePeriodGroups']['edges']
        for nn in in_ed[::-1]:
            logger.info(nn['node']['leagueMatchSetting']['leagueMatchEvent']['name'])
            for t in nn['node']['timePeriods']:
                top_id = t['id']
                top_type = base64.b64decode(top_id).decode('utf-8')
                _, search_type = top_type.split('TimePeriod-')
                _r = get_top_all_by_top_type(search_type)
                logger.info(f'search {search_type}, {len(_r or [])}')
                if _r:
                    continue
                res = await get_event_items(splt, top_id)
                parse_league(res)
    logger.info(f'get_league_player end')
