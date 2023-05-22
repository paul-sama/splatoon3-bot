
from .sp3msg import get_battle_msg_title, set_statics


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


def get_battle_msg(b_info, battle_detail, **kwargs):
    mode = b_info['vsMode']['mode']
    judgement = b_info['judgement']
    battle_detail = battle_detail['data']['vsHistoryDetail'] or {}
    title, point, b_process = get_battle_msg_title(b_info, battle_detail, **kwargs)

    # title
    msg = '#### ' + title.replace('`', '')
    msg += '''|||||||
|---|---|---|---|---|---|
'''

    # body
    text_list = []
    teams = [battle_detail['myTeam']] + battle_detail['otherTeams']
    for team in sorted(teams, key=lambda x: x['order']):
        for p in team['players']:
            text_list.append(get_row_text(p, kwargs.get('battle_show_type')))
        ti = '||'
        if mode == 'FEST':
            ti = f"|{(team.get('result') or {}).get('paintRatio') or 0:.2%}  {team.get('festTeamName')}|"
        text_list.append(f'{ti}\n')
    msg += ''.join(text_list)

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
        wave_msg += f"`EX {detail['bossResult']['boss']['name']} ({w['goldenPopCount']}) {r} {s}`\n"

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
