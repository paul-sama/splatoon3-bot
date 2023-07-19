
from .sp3msg import get_battle_msg_title, set_statics, logger, utils, get_top_str


def get_row_text(p, battle_show_type='1'):
    a, b, c = 43, 30, 20
    name = f"<img height='{a}' src='{p['headGear']['originalImage']['url']}'/>"
    name += f"<img height='{b}' src='{p['headGear']['primaryGearPower']['image']['url']}'/>"
    for g in p['headGear']['additionalGearPowers']:
        name += f"<img height='{c}' src='{g['image']['url']}'/>"

    byname = f"<img height='{a}' src='{p['clothingGear']['originalImage']['url']}'/>"
    byname += f"<img height='{b}' src='{p['clothingGear']['primaryGearPower']['image']['url']}'/>"
    for g in p['clothingGear']['additionalGearPowers']:
        byname += f"<img height='{c}' src='{g['image']['url']}'/>"

    name_id = f"<img height='{a}' src='{p['shoesGear']['originalImage']['url']}'/>"
    name_id += f"<img height='{b}' src='{p['shoesGear']['primaryGearPower']['image']['url']}'/>"
    for g in p['shoesGear']['additionalGearPowers']:
        name_id += f"<img height='{c}' src='{g['image']['url']}'/>"

    weapon_img = ((p.get('weapon') or {}).get('image2d') or {}).get('url') or ''
    weapon = f"<img height='{a}' src='{weapon_img}'/>"
    weapon += f"<img height='{b}' src='{p['weapon']['subWeapon']['image']['url']}'/>"
    weapon += f"<img height='{b}' src='{p['weapon']['specialWeapon']['image']['url']}'/>"

    img_bg = (p.get('nameplate') or {}).get('background', {}).get('image', {}).get('url', '') or ''
    name = f"{name}|{byname}|{name_id}|<img height='{a}' src='{img_bg}'/>|"
    for b in (p.get('nameplate') or {}).get('badges') or []:
        if not b:
            continue
        badge_img = (b.get('image') or {}).get('url') or ''
        name += f'<img height="{a}" src="{badge_img}"/>'
    t = f"| {weapon} | {name}|\n"
    return t


def get_row_text_image(p, battle_show_type='1'):
    re = p['result']
    if not re:
        re = {"kill": 0, "death": 99, "assist": 0, "special": 0}
    ak = re['kill']
    k = re['kill'] - re['assist']
    k_str = f'{k}+{re["assist"]}'
    d = re['death']
    ration = k / d if d else 99
    name = p['name']
    if p.get('isMyself'):
        name = f'**{name}**'

    top_str = get_top_str(p['id'])
    if top_str:
        name = name.strip() + f' `{top_str}`'

    weapon_img = ((p.get('weapon') or {}).get('image') or {}).get('url') or ''
    w_str = f'<img height="40" src="{weapon_img}"/>'
    name = f'{name}|'
    t = f"|{w_str}|{ak:>2}|{k_str:>5}k | {d:>2}d|{ration:>4.1f}|{re['special']:>3}sp| {p['paint']:>4}p| {name}|\n"
    return t


def get_battle_msg(b_info, battle_detail, **kwargs):
    logger.debug(f'get_battle_msg kwargs: {kwargs}')
    mode = b_info['vsMode']['mode']
    judgement = b_info['judgement']
    battle_detail = battle_detail['data']['vsHistoryDetail'] or {}
    title, point, b_process = get_battle_msg_title(b_info, battle_detail, **kwargs)

    get_image = kwargs.get('get_image')

    # title
    msg = '#### ' + title.replace('`', '')
    if get_image:
        msg += '''|||||||||
|---|---:|---:|---:|---|---|---|---|
    '''
    else:
        msg += '''|||||||
|---|---|---|---|---|---|
'''

    # body
    text_list = []
    teams = [battle_detail['myTeam']] + battle_detail['otherTeams']
    for team in sorted(teams, key=lambda x: x['order']):
        for p in team['players']:
            if get_image:
                text_list.append(get_row_text_image(p, kwargs.get('battle_show_type')))
            else:
                text_list.append(get_row_text(p, kwargs.get('battle_show_type')))
        ti = '||'
        if mode == 'FEST':
            ti = f"||||||||{(team.get('result') or {}).get('paintRatio') or 0:.2%}  {team.get('festTeamName')}|"
        text_list.append(f'{ti}\n')
    msg += ''.join(text_list)

    # footer
    duration = battle_detail['duration']
    score_list = []
    for t in teams:
        if (t.get('result') or {}).get('score') is not None:
            score_list.append(str((t['result']['score'])))
        elif (t.get('result') or {}).get('paintRatio') is not None:
            score_list.append(f"{t['result']['paintRatio']:.2%}"[:-2])
    score = ':'.join(score_list)
    str_open_power = ''
    str_max_open_power = ''
    last_power = ''
    if (battle_detail.get('bankaraMatch') or {}).get('mode') == 'OPEN' or battle_detail.get('leagueMatch'):
        open_power = ((battle_detail.get('bankaraMatch') or {}).get('bankaraPower') or {}).get('power') or 0
        if battle_detail.get('leagueMatch'):
            open_power = battle_detail['leagueMatch'].get('myLeaguePower') or 0

        if open_power:
            str_open_power = f'战力: {open_power:.2f}'
            current_statics = {}
            max_open_power = 0
            if 'current_statics' in kwargs:
                current_statics = kwargs['current_statics']
                max_open_power = current_statics.get('max_open_power') or 0
            max_open_power = max(max_open_power, open_power)
            last_power = current_statics.get('open_power') or 0
            get_prev = None
            if not last_power:
                get_prev = True
                prev_id = (battle_detail.get('previousHistoryDetail') or {}).get('id')
                splt = kwargs.get('splt')
                if splt:
                    prev_info = splt.get_battle_detail(prev_id)
                    if prev_info:
                        prev_detail = prev_info.get('data', {}).get('vsHistoryDetail') or {}
                        prev_open_power = ((prev_detail.get('bankaraMatch') or {}).get('bankaraPower') or {}).get('power') or 0
                        if prev_detail and not prev_open_power:
                            prev_open_power = (prev_detail.get('leagueMatch') or {}).get('myLeaguePower') or 0
                        if prev_open_power:
                            last_power = prev_open_power

            if last_power:
                diff = open_power - last_power
                if diff:
                    str_open_power = f"战力: ({diff:+.2f}) {open_power:.2f}"
            if max_open_power and not get_prev:
                str_max_open_power = f', MAX: {max_open_power:.2f}'
            current_statics['open_power'] = open_power
            current_statics['max_open_power'] = max_open_power

    str_open_power_inline = ''
    if str_open_power and ('current_statics' in kwargs or last_power):
        msg += f"\n####{str_open_power}{str_max_open_power}\n"
    elif str_open_power:
        str_open_power_inline = str_open_power
    msg += f"\n#### duration: {duration}s, {score} knockout: {battle_detail['knockout']} {b_process} {str_open_power_inline}"

    return msg


def coop_row(p):
    weapon = f"<img height='18' src='{p['specialWeapon']['image']['url']}'/> |"
    for w in p['weapons']:
        weapon += f"<img height='18' src='{w['image']['url']}'/>"
    return f"|x{p['defeatEnemyCount']}| {p['goldenDeliverCount']} |{p['rescuedCount']}d |" \
           f"{p['deliverCount']} |{p['rescueCount']}r| {p['player']['name']}|{weapon}|"


def get_coop_msg(coop_info, data):
    c_point = coop_info.get('coop_point')
    c_eggs = coop_info.get('coop_eggs')
    detail = data['data']['coopHistoryDetail']
    my = detail['myResult']
    wave_msg = '''| | | |  |
| -- | --: |--|--|
'''
    d_w = {0: '∼', 1: '≈', 2: '≋'}
    win = False
    total_deliver_cnt = 0
    wave_cnt = 3
    if detail.get('rule') == 'TEAM_CONTEST':
        wave_cnt = 5
    for w in detail['waveResults'][:wave_cnt]:
        event = (w.get('eventWave') or {}).get('name') or ''
        specs = ''
        for s in w.get('specialWeapons') or []:
            img = s['image']['url']
            specs += f'<img height="18" src="{img}"/>'
        wave_msg += f"|W{w['waveNumber']} | {w['teamDeliverCount']}/{w['deliverNorm']}({w['goldenPopCount']}) |" \
                    f"{d_w[w['waterLevel']]} {event}| {specs} |\n"
        total_deliver_cnt += w['teamDeliverCount'] or 0
        if w['waveNumber'] == 3 and w['teamDeliverCount'] >= w['deliverNorm']:
            win = True
    if detail.get('bossResult'):
        w = detail['waveResults'][-1]
        r = 'GJ!' if detail['bossResult']['hasDefeatBoss'] else 'NG'
        s = ''
        scale = detail.get('scale')
        if scale and scale.get('gold'):
            s += f' 🏅️{scale["gold"]}'
        if scale and scale.get('silver'):
            s += f' 🥈{scale["silver"]}'
        if scale and scale.get('bronze'):
            s += f' 🥉{scale["bronze"]}'
        wave_msg += f"EX |{detail['bossResult']['boss']['name']} ({w['goldenPopCount']}) |{r} {s}||\n"

    if total_deliver_cnt and c_eggs:
        total_deliver_cnt = f'{total_deliver_cnt} ({c_eggs})'

    king_smell = detail.get("smellMeter")
    king_str = f'{king_smell}/5' if king_smell else ''
    msg = f"""
#### {detail['afterGrade']['name'] if detail.get('afterGrade') else ''} {detail['afterGradePoint'] or ''} {detail['dangerRate']:.0%} {'🎉 ' if win else ''}+{detail['jobPoint']}({c_point}p) {king_str}
{wave_msg}

#### {total_deliver_cnt}
|  |   ||  |||||
| --: |--:|--:|--:|--|--|--|--|
{coop_row(my)}
"""
    for p in detail['memberResults']:
        msg += f"""{coop_row(p)}\n"""
    msg += '''\n|        | |||
|-------:|--|--|--|
'''
    for e in detail['enemyResults']:
        c = str(e.get('teamDefeatCount') or 0)
        nice = ''
        if e.get('popCount') <= int(c):
            nice = '√'
        img_str = f"<img height='18' src='{e['enemy']['image']['url']}'/>"
        msg += f"""|{e.get('teamDefeatCount') or ''} |{e['defeatCount'] or ''} |{e['popCount'] or ''} | {img_str} {(e.get('enemy') or {}).get('name') or ''} {nice}|\n"""
    # logger.info(msg)
    return msg


def get_history(splt, _type='open'):
    logger.info(f'get history {_type}')
    data = None
    if _type == 'event':
        data = utils.gen_graphql_body(utils.translate_rid['EventBattleHistoriesQuery'])
    elif _type == 'open':
        data = utils.gen_graphql_body(utils.translate_rid['BankaraBattleHistoriesQuery'])
    elif _type == 'fest':
        data = utils.gen_graphql_body(utils.translate_rid['RegularBattleHistoriesQuery'])

    res = splt._request(data)
    if not res:
        return 'No battle found!'

    msg = ''
    event_h = []
    if _type == 'event':
        event_h = res['data']['eventBattleHistories']['historyGroups']['nodes']
    if _type == 'open':
        event_h = res['data']['bankaraBattleHistories']['historyGroups']['nodes']
    if _type == 'fest':
        event_h = res['data']['regularBattleHistories']['historyGroups']['nodes']
        new_event_h = []
        for g in event_h:
            for n in g['historyDetails']['nodes']:
                # 单排 fest
                if n['vsMode']['id'] == 'VnNNb2RlLTc=':
                    new_event_h.append(g)
                    break
        event_h = new_event_h

    for g_node in event_h:
        msg += get_group_node_msg(g_node, splt, _type)
        break

    # logger.info(msg)
    if not msg:
        return f'No battle {_type} found!'
    return msg


def get_group_node_msg(g_node, splt, _type):
    msg = ''
    battle_lst = []
    if _type == 'event':
        msg = '#### ' + g_node['leagueMatchHistoryGroup']['leagueMatchEvent']['name'] + '\n'
        battle_lst = g_node['historyDetails']['nodes']
    elif _type == 'open':
        msg = f"#### 开放: {g_node['historyDetails']['nodes'][0]['vsRule']['name']}\n"
        battle_lst = []
        stage_lst = []
        for n in g_node['historyDetails']['nodes']:
            if 'bankaraMatch' not in n or 'earnedUdemaePoint' not in n['bankaraMatch']:
                continue
            stage_name = n['vsStage']['name']
            if stage_name not in stage_lst:
                stage_lst.append(stage_name)
            # 最新一个时段
            if len(stage_lst) > 2:
                break
            battle_lst.append(n)
    elif _type == 'fest':
        msg = f"#### 祭典单排\n"
        battle_lst = g_node['historyDetails']['nodes']

    msg += '''
|  |   ||  ||||||||||
| --: |--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--|
'''

    dict_p = {}
    last_power = 0
    for b in battle_lst[::-1]:
        _id = b['id']
        dict_p[_id] = {}
        _data = utils.gen_graphql_body(utils.translate_rid['VsHistoryDetailQuery'], varname='vsResultId', varvalue=_id)
        battle_detail = splt._request(_data)
        if not battle_detail:
            continue
        cur_power = 0
        if _type == 'event':
            cur_power = battle_detail['data']['vsHistoryDetail']['leagueMatch']['myLeaguePower']
        elif _type == 'open':
            b_d = battle_detail['data']['vsHistoryDetail'].get('bankaraMatch') or {}
            cur_power = (b_d.get('bankaraPower') or {}).get('power')
        elif _type == 'fest':
            b_d = battle_detail['data']['vsHistoryDetail'].get('festMatch') or {}
            cur_power = b_d.get('myFestPower')

        if cur_power:
            dict_p[_id] = {'cur': cur_power, 'diff': cur_power - last_power if last_power else ''}
        last_power = cur_power

        b_detail = battle_detail['data']['vsHistoryDetail']
        my_str = get_my_row(b_detail['myTeam'])
        duration = b_detail['duration']

        score_list = []
        for t in [b_detail['myTeam']] + b_detail['otherTeams']:
            if (t.get('result') or {}).get('score') is not None:
                score_list.append(str((t['result']['score'])))
            elif (t.get('result') or {}).get('paintRatio') is not None:
                score_list.append(f"{t['result']['paintRatio']:.2%}"[:-2])
        score = ':'.join(score_list)
        dict_p[_id].update({'my_str': my_str, 'duration': duration, 'score': score})

    for n in battle_lst:
        _id = n['id']
        if _id not in dict_p:
            continue
        p = dict_p.get(_id) or {}
        if p.get('diff'):
            str_p = f'{p["diff"]:+.2f}|'
        else:
            str_p = '      |'

        if p.get('cur'):
            str_p += f' {p["cur"]:.2f}'
        else:
            str_p += '        '

        my_str = p.get('my_str') or ''
        weapon_img = (((n.get('player') or {}).get('weapon') or {}).get('image') or {}).get('url') or ''
        weapon_str = f'<img height="20" src="{weapon_img}"/>'
        duration = p.get('duration') or ''
        score = p.get('score') or ''
        jud = n.get('judgement') or ''
        if jud not in ('WIN', 'LOSE'):
            jud = 'DRAW'
        row = f"|{jud}| {str_p}| {weapon_str}|{my_str}| {duration}s|{score}| {n['vsStage']['name'][:8]}"

        msg += row + '\n'
    msg += '||\n'
    return msg


def get_my_row(my_team):
    p = {}
    for _p in my_team['players']:
        if _p.get('isMyself'):
            p = _p
            break

    re = p['result']
    if not re:
        re = {"kill": 0, "death": 99, "assist": 0, "special": 0}
    ak = re['kill']
    k = re['kill'] - re['assist']
    k_str = f'{k}+{re["assist"]}'
    d = re['death']
    ration = k / d if d else 99

    t = f"{ak:>2}|{k_str:>5}k| {d:>2}d|{ration:>4.1f}|{re['special']:>3}sp| {p['paint']:>4}p "
    return t
