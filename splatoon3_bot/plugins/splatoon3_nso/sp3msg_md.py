import base64
from datetime import timedelta, datetime as dt
from .sp3msg import get_battle_msg_title, set_statics, logger, utils, get_top_str, defaultdict, fmt_sp3_state
from .db_sqlite import (
    model_get_user_friend, model_get_login_user, get_top_all, get_top_all_row, get_weapon, model_get_report,
    get_top_player_row, get_temp_image_path, UserFriendTable
)


async def get_row_text(p, battle_show_type='1'):
    """获取一行对战玩家信息
    p:player的一个遍历对象
    """
    a, b, c = 43, 30, 20

    # 上衣
    img_type = "battle_headGear"
    img1 = await get_temp_image_path(img_type, p['headGear']['name'], p['headGear']['originalImage']['url'])
    head_gear = f"<img height='{a}' src='{img1}'/>"

    img_type = "battle_primaryGearPower"
    img2 = await get_temp_image_path(img_type, p['headGear']['primaryGearPower']['name'],
                                     p['headGear']['primaryGearPower']['image']['url'])
    head_gear += f"<img height='{b}' src='{img2}'/>"

    for g in p['headGear']['additionalGearPowers']:
        img_type = "battle_additionalGearPowers"
        img3 = await get_temp_image_path(img_type, g['name'], g['image']['url'])
        head_gear += f"<img height='{c}' src='{img3}'/>"

    # 服装
    img_type = "battle_clothingGear"
    img1 = await get_temp_image_path(img_type, p['clothingGear']['name'], p['clothingGear']['originalImage']['url'])
    clothing_gear = f"<img height='{a}' src='{img1}'/>"

    img_type = "battle_primaryGearPower"
    img2 = await get_temp_image_path(img_type, p['clothingGear']['primaryGearPower']['name'],
                                     p['clothingGear']['primaryGearPower']['image']['url'])
    clothing_gear += f"<img height='{b}' src='{img2}'/>"

    for g in p['clothingGear']['additionalGearPowers']:
        img_type = "battle_additionalGearPowers"
        img3 = await get_temp_image_path(img_type, g['name'], g['image']['url'])
        clothing_gear += f"<img height='{c}' src='{img3}'/>"

    # 鞋子
    img_type = "battle_shoesGear"
    img1 = await get_temp_image_path(img_type, p['shoesGear']['name'], p['shoesGear']['originalImage']['url'])
    shoes_gear = f"<img height='{a}' src='{img1}'/>"

    img_type = "battle_primaryGearPower"
    img2 = await get_temp_image_path(img_type, p['shoesGear']['primaryGearPower']['name'],
                                     p['shoesGear']['primaryGearPower']['image']['url'])
    shoes_gear += f"<img height='{b}' src='{img2}'/>"

    for g in p['shoesGear']['additionalGearPowers']:
        img_type = "battle_additionalGearPowers"
        img3 = await get_temp_image_path(img_type, g['name'], g['image']['url'])
        shoes_gear += f"<img height='{c}' src='{img3}'/>"

    # 武器
    weapon_img = ((p.get('weapon') or {}).get('image2d') or {}).get('url') or ''
    weapon_name = ((p.get('weapon') or {}).get('name') or '')
    img_type = "battle_weapon_main"
    img1 = await get_temp_image_path(img_type, weapon_name, weapon_img)
    weapon = f"<img height='{a}' src='{img1}'/>"

    img_type = "battle_weapon_sub"
    img2 = await get_temp_image_path(img_type, p['weapon']['subWeapon']['name'],
                                     p['weapon']['subWeapon']['image']['url'])
    weapon += f"<img height='{b}' src='{img2}'/>"

    img_type = "battle_weapon_special"
    img3 = await get_temp_image_path(img_type, p['weapon']['specialWeapon']['name'],
                                     p['weapon']['specialWeapon']['image']['url'])
    weapon += f"<img height='{b}' src='{img3}'/>"

    # 获取好友数据库的步骤是通过好友列表实现的，但好友列表只提供了game_name，没有提供name_id，此处搜索只能粗略判断
    r: UserFriendTable = model_get_user_friend(p['name'])
    if r:
        img_type = "friend_icon"
        # 储存名使用friend_id
        img = await get_temp_image_path(img_type, r.friend_id, r.user_icon)
        weapon += f"<img height='{a}' style='position:absolute;left:10px' src='{img}'/>"
    # # 用户其他信息无需联动好友数据库，储存名改为 game_name + name_id 唯一标识    暂未使用
    # game_name = f"{p['name']}#{p['nameId']}"

    img_type = "user_nameplate_bg"
    img_bg = await get_temp_image_path(img_type, p['nameplate']['background']['id'],
                                       p['nameplate']['background']['image']['url'])
    name = f"{head_gear}|{clothing_gear}|{shoes_gear}|<img height='{a}' src='{img_bg}'/>|"
    for b in (p.get('nameplate') or {}).get('badges') or []:
        if not b:
            continue
        badge_img = (b.get('image') or {}).get('url') or ''
        if badge_img != "":
            img_type = "user_nameplate_badge"
            img_badge = await get_temp_image_path(img_type, b['id'], badge_img)
            name += f'<img height="{a}" src="{img_badge}"/>'
    t = f"| {weapon} | {name}|\n"
    return t


async def get_user_name_color(nick_name, player_code):
    r_l = model_get_login_user(player_code)
    # 登录用户绿色
    if r_l:
        return f'<span style="color:green">{nick_name}</span>'

    u_str = nick_name
    r = model_get_user_friend(nick_name)
    # 用户好友蓝色
    if r:
        img_type = "friend_icon"
        # 储存名使用friend_id
        user_icon = await get_temp_image_path(img_type, r.friend_id, r.user_icon)
        img = f"<img height='36px' style='position:absolute;right:5px;margin-top:-6px' src='{user_icon}'/>"
        u_str = f'<span style="color:skyblue">{nick_name} {img}</span>'
    return u_str


async def get_top_all_name(name, player_code):
    top_all = get_top_all_row(player_code)
    if not top_all:
        return name

    row = top_all
    max_power = row.power
    top_str = f'F({max_power})' if row.top_type.startswith('Fest') else f'E({max_power})'
    name = name.replace('`', '&#96;').replace('|', '&#124;')
    name = name.strip() + f' <span style="color:#EE9D59">`{top_str}`</span">'
    if '<img' not in name:
        weapon_id = str(row.weapon_id)
        weapon = get_weapon() or {}
        if weapon.get(weapon_id):
            img_type = "weapon_main"
            weapon_main_img = await get_temp_image_path(img_type, weapon[weapon_id]['name'], weapon[weapon_id]['url'])
            name += f"<img height='36px' style='position:absolute;right:5px;margin-top:-6px' src='{weapon_main_img}'/>"
    return name


async def get_top_str_w(player_code):
    top_str = ''
    r = get_top_player_row(player_code)
    if r:
        _x = 'x' if ':6:' in r.top_type else 'X'
        if '-a:' in r.top_type:
            top_str = f' <span style="color:#fc0390">{_x}{r.rank}</span"><span style="color:red">({r.power})</span">'
        else:
            top_str = f' <span style="color:red">{_x}{r.rank}({r.power})</span">'
        weapon_id = str(r.weapon_id)
        weapon = get_weapon() or {}
        if weapon.get(weapon_id):
            img_type = "weapon_main"
            weapon_main_img = await get_temp_image_path(img_type, weapon[weapon_id]['name'], weapon[weapon_id]['url'])
            top_str += f"<img height='36px' style='position:absolute;right:5px;margin-top:-6px' src='{weapon_main_img}'/>"
        return top_str
    return top_str


async def get_row_text_image(p, mask=False):
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
        name = f'<b>{name}</b>'
    elif mask:
        name = f'~~我是马赛克~~'

    player_code = (base64.b64decode(p['id']).decode('utf-8') or '').split(':u-')[-1]
    if not p.get('isMyself'):
        name = await get_user_name_color(name, player_code)

    top_str = await get_top_str_w(player_code)
    if top_str:
        name = name.strip() + top_str

    elif not p.get('isMyself'):
        name = await get_top_all_name(name, player_code)

    weapon_img = ((p.get('weapon') or {}).get('image') or {}).get('url') or ''
    img_type = "weapon_main"
    weapon_main_img = await get_temp_image_path(img_type, p['weapon']['name'], weapon_img)
    w_str = f'<img height="40" src="{weapon_main_img}"/>'
    name = f'{name}|'
    t = f"|{w_str}|{ak:>2}|{k_str:>5}k | {d:>2}d|{ration:>4.1f}|{re['special']:>3}sp| {p['paint']:>4}p| {name}|\n"
    return t


async def get_battle_msg(b_info, battle_detail, **kwargs):
    # logger.info(f'battle_detail: {battle_detail}')
    logger.debug(f'get_battle_msg kwargs: {kwargs}')
    mode = b_info['vsMode']['mode']
    judgement = b_info['judgement']
    battle_detail = battle_detail['data']['vsHistoryDetail'] or {}
    title, point, b_process = await get_battle_msg_title(b_info, battle_detail, **kwargs)

    get_image = kwargs.get('get_image')
    mask = kwargs.get('mask')

    # title
    msg = '#### ' + title.replace('`', '')
    if get_image:
        msg += '''|||||||||
|---|---:|---:|---:|---:|---:|---:|---|
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
                text_list.append(await get_row_text_image(p, mask))
            else:
                text_list.append(await get_row_text(p, mask))
        ti = '||'
        if mode == 'FEST':
            _str_team = f"{(team.get('result') or {}).get('paintRatio') or 0:.2%}  {team.get('festTeamName')}"
            _c = team.get('color') or {}
            if _c and 'r' in _c:
                _str_color = f"rgba({int(_c['r'] * 255)}, {int(_c['g'] * 255)}, {int(_c['b'] * 255)}, {_c['a']})"
                _str_team = f"<span style='color:{_str_color}'>{_str_team}</span>"
            ti = f"||||||||{_str_team}|"
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
    if (not mask and get_image and
            ((battle_detail.get('bankaraMatch') or {}).get('mode') == 'OPEN' or
             battle_detail.get('leagueMatch') or
             mode == 'FEST')):
        open_power = ((battle_detail.get('bankaraMatch') or {}).get('bankaraPower') or {}).get('power') or 0
        if battle_detail.get('leagueMatch'):
            open_power = battle_detail['leagueMatch'].get('myLeaguePower') or 0
        if mode == 'FEST':
            open_power = (battle_detail.get('festMatch') or {}).get('myFestPower') or 0

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
                    prev_info = await splt.get_battle_detail(prev_id)
                    if prev_info:
                        prev_detail = prev_info.get('data', {}).get('vsHistoryDetail') or {}
                        prev_open_power = ((prev_detail.get('bankaraMatch') or {}).get('bankaraPower') or {}).get(
                            'power') or 0
                        if prev_detail and not prev_open_power:
                            prev_open_power = (prev_detail.get('leagueMatch') or {}).get('myLeaguePower') or 0
                        if mode == 'FEST' and prev_detail and not prev_open_power:
                            prev_open_power = (prev_detail.get('festMatch') or {}).get('myFestPower') or 0
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

        # 开放重新定分置零
        if (not open_power and judgement in ('WIN', 'LOST') and
                (kwargs.get('current_statics') or {}).get('max_open_power')):
            current_statics = kwargs['current_statics']
            current_statics['open_power'] = 0
            current_statics['max_open_power'] = 0

    str_open_power_inline = ''
    if str_open_power and ('current_statics' in kwargs or last_power):
        msg += f"\n####{str_open_power}{str_max_open_power}\n"
    elif str_open_power:
        str_open_power_inline = str_open_power

    try:
        date_play = dt.strptime(battle_detail['playedTime'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)
        str_time = (date_play + timedelta(seconds=duration)).strftime('%y-%m-%d %H:%M:%S')
    except Exception as e:
        str_time = ''
    msg += f"\n#### duration: {duration}s, {str_time}, {score} {b_process} {str_open_power_inline}"

    succ = 0
    if 'current_statics' in kwargs:
        current_statics = kwargs['current_statics']
        set_statics(current_statics=current_statics, judgement=judgement, point=point, battle_detail=battle_detail)
        succ = current_statics['successive']

    if abs(succ) >= 3:
        if succ > 0:
            msg += f', {succ}连胜'
        else:
            msg += f', {abs(succ)}连败'

    dict_a = {'GOLD': '🏅️', 'SILVER': '🥈', 'BRONZE': '🥉'}
    award_list = [f"{dict_a.get(a['rank'], '')}{a['name']}" for a in battle_detail['awards']]
    msg += ('\n ' + ' '.join(award_list) + '\n')

    if mode == 'FEST':
        msg += f'\n#### {b_info["player"]["festGrade"]}'

    # push mode
    if 'current_statics' in kwargs:
        current_statics = kwargs['current_statics']
        total = current_statics.get('TOTAL') or 0
        win = current_statics.get('WIN') or 0
        lose = total - win
        if total:
            str_static = f'{win}-{lose}'
            k = current_statics.get('K') or 0
            a = current_statics.get('A') or 0
            d = current_statics.get('D') or 0
            if k or a or d:
                str_static += f' {k}+{a}k/{d}d'
            # 2-1 9+2k/8d
            msg += f'\n#### {str_static}'

    return msg


async def coop_row(p, mask=False, is_myself=False):
    try:
        img_type = "coop_special"
        special_img = await get_temp_image_path(img_type, p['specialWeapon']['name'], p['specialWeapon']['image']['url'])
        weapon = f"<img height='18' src='{special_img}'/> |"
        for w in p['weapons']:
            img_type = "coop_weapon"
            weapon_img = await get_temp_image_path(img_type, w['name'], w['image']['url'])
            weapon += f"<img height='18' src='{weapon_img}'/>"
    except Exception as e:
        logger.warning(f'coop_row error: {e}')
        weapon = 'w|'

    p_name = p['player']['name']
    img_type = "coop_uniform"
    uniform_img = await get_temp_image_path(img_type, p["player"]["uniform"]['name'], p["player"]["uniform"]["image"]["url"])
    img_str = f'<img height="18" src="{uniform_img}"/>'

    if mask:
        p_name = f'~~我是马赛克~~'

    if not is_myself:
        player_code = (base64.b64decode(p["player"]['id']).decode('utf-8') or '').split(':u-')[-1]
        p_name = await get_user_name_color(p_name, player_code)

    return f"|x{p['defeatEnemyCount']}| {p['goldenDeliverCount']} |{p['rescuedCount']}d |" \
           f"{p['deliverCount']} |{p['rescueCount']}r| {img_str} {p_name}|{weapon}|"


async def get_coop_msg(coop_info, data, **kwargs):
    c_point = coop_info.get('coop_point')
    c_eggs = coop_info.get('coop_eggs')
    detail = data['data']['coopHistoryDetail']
    mask = kwargs.get('mask')
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
            img_type = "coop_special"
            img = await get_temp_image_path(img_type, s['name'], s['image']['url'])
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
    h_grade = detail['afterGrade']['name'] if detail.get('afterGrade') else ''
    h_point = detail['afterGradePoint'] or ''

    msg = f"""
#### {h_grade} {h_point} {detail['dangerRate']:.0%} {'🎉 ' if win else ''}+{detail['jobPoint']}({c_point}p) {king_str}
{wave_msg}

#### {total_deliver_cnt}
|  |   ||  |||||
| --: |--:|--:|--:|--|--|--|--|
{await coop_row(my, is_myself=True)}
"""
    for p in detail['memberResults']:
        msg += f"""{await coop_row(p, mask=mask)}\n"""
    msg += '''\n|        | ||
|-------|--:|--|
'''
    for e in detail['enemyResults']:
        nice = ''
        if e.get('popCount', 0) <= int(str(e.get('teamDefeatCount') or 0)):
            nice = '√'
        boss_cnt = e.get('teamDefeatCount') or 0
        boss_pop = e['popCount'] or ''
        if e.get('defeatCount'):
            boss_cnt = f'{boss_cnt}({e["defeatCount"]})'
        img_type = "coop_boss"
        img_name = (e.get('enemy') or {}).get('name') or ''
        img_url = e['enemy']['image']['url']
        img = await get_temp_image_path(img_type, img_name, img_url)
        img_str = f"<img height='18' src='{img}'/>"
        boss_name = f"{img_str} {img_name}"
        if nice:
            boss_cnt = f'<span style="color: green">{boss_cnt}</span>'
            boss_pop = f'<span style="color: green">{boss_pop}</span>'
            boss_name = f'<span style="color: green">{boss_name}</span>'
        msg += f"""|{boss_cnt} |{boss_pop} | {boss_name}|\n"""

    try:
        date_play = dt.strptime(detail['playedTime'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)
        str_time = date_play.strftime('%y-%m-%d %H:%M:%S')
        msg += f"\n##### HKT {str_time}"
    except Exception as e:
        pass

    # logger.info(msg)
    return msg


async def get_history(splt, _type='open'):
    logger.info(f'get history {_type}')
    data = None
    if _type == 'event':
        data = utils.gen_graphql_body(utils.translate_rid['EventBattleHistoriesQuery'])
    elif _type == 'open':
        data = utils.gen_graphql_body(utils.translate_rid['BankaraBattleHistoriesQuery'])
    elif _type == 'fest':
        data = utils.gen_graphql_body(utils.translate_rid['RegularBattleHistoriesQuery'])

    res = await splt._request(data)
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
        msg += await get_group_node_msg(g_node, splt, _type)
        break

    # logger.info(msg)
    if not msg:
        return f'No battle {_type} found!'
    return msg


async def get_group_node_msg(g_node, splt, _type):
    msg = ''
    battle_lst = []
    if _type == 'event':
        battle_lst = g_node['historyDetails']['nodes']
        fst_battle = battle_lst[0]
        battle_id = fst_battle['id']
        battle_t = base64.b64decode(battle_id).decode('utf-8').split('_')[0].split(':')[-1]
        b_t = dt.strptime(battle_t, '%Y%m%dT%H%M%S') + timedelta(hours=8)
        msg = '#### ' + g_node['leagueMatchHistoryGroup']['leagueMatchEvent'][
            'name'] + f' HKT {b_t:%Y-%m-%d %H:%M:%S}\n'
    elif _type == 'open':
        fst_battle = g_node['historyDetails']['nodes'][0]
        battle_id = fst_battle['id']
        battle_t = base64.b64decode(battle_id).decode('utf-8').split('_')[0].split(':')[-1]
        b_t = dt.strptime(battle_t, '%Y%m%dT%H%M%S') + timedelta(hours=8)
        msg = f"#### 开放: {fst_battle['vsRule']['name']} HKT {b_t:%Y-%m-%d %H:%M:%S}\n"
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
        battle_lst = g_node['historyDetails']['nodes']
        b_lst = []
        for b in battle_lst:
            if b['vsMode']['id'] == 'VnNNb2RlLTc=':
                b_lst.append(b)
        battle_lst = b_lst
        fst_battle = battle_lst[0]
        battle_id = fst_battle['id']
        battle_t = base64.b64decode(battle_id).decode('utf-8').split('_')[0].split(':')[-1]
        b_t = dt.strptime(battle_t, '%Y%m%dT%H%M%S') + timedelta(hours=8)
        msg = f"#### 祭典单排 HKT {b_t:%Y-%m-%d %H:%M:%S}\n"

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
        battle_detail = await splt._request(_data)
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

        img_type = "weapon_main"
        weapon_main_img = await get_temp_image_path(img_type, n['player']['weapon']['name'], weapon_img)
        weapon_str = f'<img height="20" src="{weapon_main_img}"/>'
        duration = p.get('duration') or ''
        score = p.get('score') or ''
        jud = n.get('judgement') or ''
        if jud not in ('WIN', 'LOSE'):
            jud = 'DRAW'
        row = f"|{jud}| {str_p}| {weapon_str}|{my_str}| {duration}s|{score}| {n['vsStage']['name'][:7]}"

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


def get_cn_cp3_stat(_st):
    if 'PRIVATE' in _st:
        _st = '私房'
    elif 'X_MATCH)' in _st:
        _st = 'X比赛'
    elif 'RA)O' in _st:
        _st = '开放'
    elif 'RA)C' in _st:
        _st = '挑战'
    elif 'MATCHING' in _st:
        _st = '匹配中'
    elif 'COOP' in _st:
        _st = '打工'
    elif 'REGULAR)' in _st:
        _st = '涂地'
    elif _st == 'ONLINE':
        _st = '在线'
    elif 'LEAGUE' in _st:
        _st = '活动'
    elif 'FEST)O' in _st:
        _st = '祭典开放'
    elif 'FEST)C' in _st:
        _st = '祭典挑战'
    elif 'FEST)3' in _st:
        _st = '祭典三色'
    return _st


async def get_friends(splt, lang='zh-CN'):
    data = utils.gen_graphql_body(utils.translate_rid['FriendsList'])
    res = await splt._request(data)
    if not res:
        return '网络错误，请稍后再试.'

    msg = f'''#### 在线好友 HKT {dt.now():%Y-%m-%d %H:%M:%S}
||||||
|---:|---|:---|:---|---|
'''
    _dict = defaultdict(int)
    for f in res['data']['friends']['nodes']:
        if f.get('onlineState') == 'OFFLINE':
            continue
        _state = fmt_sp3_state(f)
        _state = get_cn_cp3_stat(_state)

        _dict[_state] += 1
        n = f['playerName'] or f.get('nickname')

        img_type = "friend_icon"
        # 储存名使用friend_id
        icon_img = await get_temp_image_path(img_type, f['id'], f['userIcon']['url'])
        img = f'''<img height="40" src="{icon_img}"/>'''
        if f['playerName'] and f['playerName'] != f['nickname']:
            nickname = f['nickname'].replace("|", "\|").replace('`', '')
            n = f'{f["playerName"]}|{img}|{nickname}'
        else:
            n = f'{n}|{img}|'
        msg += f'''|{n}| {_state}|\n'''

    msg += '||\n'
    _dict['TOTAL'] = sum(_dict.values())
    for k, v in _dict.items():
        msg += f'||||{k}| {v}|\n'
    msg += '||\n'
    return msg


async def get_ns_friends(splt):
    res = splt.app_ns_friend_list() or {}
    res = res.get('result')
    if not res:
        logger.info(res)
        return 'No friends found!'

    get_sp3 = False

    for f in res.get('friends') or []:
        if (f.get('presence') or {}).get('state') != 'ONLINE':
            continue
        if f['presence']['game'].get('name') == 'Splatoon 3':
            get_sp3 = True
            break

    dict_sp3 = {}
    _dict_sp3 = defaultdict(int)
    if get_sp3:
        data = utils.gen_graphql_body(utils.translate_rid['FriendsList'])
        sp3_res = await splt._request(data) or []
        if sp3_res:
            for f in sp3_res['data']['friends']['nodes']:
                if f.get('onlineState') == 'OFFLINE':
                    continue
                _state = fmt_sp3_state(f)
                if _state == 'ONLINE':
                    continue
                _state = get_cn_cp3_stat(_state)
                dict_sp3[f.get('nickname')] = _state
                _dict_sp3[_state] += 1

    msg = f'''#### NS在线好友 HKT {dt.now():%Y-%m-%d %H:%M:%S}
|||||
|---:|---|---|:---|
'''
    _dict = defaultdict(int)
    for f in res.get('friends') or []:
        if (f.get('presence') or {}).get('state') != 'ONLINE' and f.get('isFavoriteFriend') is False:
            continue
        u_name = f.get('name') or ''
        u_name = u_name.replace("|", "\|")

        img_type = "ns_friend_icon"
        # 储存名使用friend_id
        icon_img = await get_temp_image_path(img_type, f['nsaId'], f['imageUri'])
        img_str = f'''<img height="40" src="{icon_img}"/>'''
        msg += f'|{u_name}|{img_str}'
        if (f.get('presence') or {}).get('state') == 'ONLINE':
            _game_name = f['presence']['game'].get('name') or ''
            _game_name = _game_name.replace('The Legend of Zelda: Tears of the Kingdom', 'TOTK')
            msg += f"|{_game_name}"
            _dict[_game_name] += 1
            if f['presence']['game'].get('totalPlayTime'):
                msg += f"({int(f['presence']['game'].get('totalPlayTime') / 60)}h)|"
            else:
                msg += '|'
            if f.get('name') in dict_sp3:
                msg += f" {dict_sp3[f.get('name')]}|"
            else:
                msg += '|'
        else:
            t = (f.get('presence') or {}).get('logoutAt') or 0
            if t:
                delt = str(dt.utcnow() - dt.utcfromtimestamp(t))
                tt = delt
                if tt.startswith('0'):
                    tt = tt.split(', ')[-1]
                tt = tt.split('.')[0][:-3].replace(':', 'h')
                msg += f" |(offline about {tt})||"
            else:
                msg += f" |({(f.get('presence') or {}).get('state', 'offline')})||"
        msg += '\n'
    st = ''
    _dict['total online'] = sum(_dict.values())
    _dict['total'] = len(res.get('friends') or [])
    for k, v in _dict.items():
        st += f'|||{k}| {v}|\n'

    if _dict_sp3:
        _dict_sp3['total sp3'] = sum(_dict_sp3.values())
        st += '|||||\n'
        for k, v in _dict_sp3.items():
            st += f'|||{k}| {v}|\n'

    msg = f'''
{msg}|||||
{st}
'''
    return msg


async def get_top_md(player_code):
    logger.info(f'get top md {player_code}')
    msg = ''
    dict_p = {}
    if isinstance(player_code, str):
        res = get_top_all(player_code)
        if not res:
            return msg
        res = sorted(res, key=lambda x: x.play_time)
        res = res[-30:]
    else:
        res_a = []
        for p in player_code or []:
            p, _name = p.split('_', 1)
            dict_p[p] = _name
            res = get_top_all(p)
            res = sorted(res, key=lambda x: x.play_time)
            res_a.extend(res)
        res = res_a

    # for i in res:
    #     logger.info(f'{i.top_type}, {i.rank}, {i.power}, {i.weapon}')

    if not res:
        return

    weapon = get_weapon() or {}

    str_player_code = ''
    if isinstance(player_code, str):
        str_player_code = f'({player_code})'

    msg = f'''#### 排行榜数据 {str_player_code} HKT {dt.now():%Y-%m-%d %H:%M:%S}
|||||||
|---|---:|:---|---|---|---|
'''

    if isinstance(player_code, list):
        msg = f'''#### 排行榜数据 {str_player_code} HKT {dt.now():%Y-%m-%d %H:%M:%S}
||||||||
|---|---:|:---|---|---|---|---|
'''

    p_code = ''
    if res:
        p_code = res[0].player_code
    for i in res:
        t_type = i.top_type
        if 'LeagueMatchRankingTeam' in t_type:
            t_lst = t_type.split(':')
            t_type = f'{t_lst[0]}:{t_lst[3]}'
            i.play_time += timedelta(hours=8)
        t_type = t_type.replace('LeagueMatchRankingTeam-', 'L-')
        _t = f"{i.play_time:%y-%m-%d %H}".replace(' 00', '')
        if weapon.get(str(i.weapon_id)):
            img_type = "weapon_main"
            weapon_main_img = await get_temp_image_path(img_type, weapon[str(i.weapon_id)]['name'], weapon[str(i.weapon_id)]['url'])
            str_w = f'<img height="40" src="{weapon_main_img}"/>'
        else:
            str_w = f'{i.weapon}'
        if i.player_code != p_code:
            msg += f'||\n'
            p_code = i.player_code
        if isinstance(player_code, str):
            msg += f'{t_type}|{i.rank}|{i.power}|{str_w}|{i.player_name}|{_t}\n'
        else:
            msg += f'{t_type}|{i.rank}|{i.power}|{str_w}|{i.player_name}|{dict_p[i.player_code]}|{_t}\n'

    msg += '||\n\n说明: /top [1-50] [a-h] [last]. 对战数字, 玩家排序, 全部查询\n'
    return msg


def get_summary_md(data, all_data, coop, from_group=False):

    player = data['data']['currentPlayer']
    history = data['data']['playHistory']
    start_time = history['gameStartTime']
    s_time = dt.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)
    c_time = dt.strptime(history['currentTime'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)

    all_cnt = ''
    r = ''
    if all_data:
        total_cnt = all_data['data']['playHistory']['battleNumTotal']
        all_cnt = f"/{total_cnt}"
        if total_cnt:
            r = f"{history['winCountTotal'] / total_cnt:.2%}"

    coop_msg = ''
    if coop:
        coop = coop['data']['coopResult']
        card = coop['pointCard']
        p = coop['scale']
        name = f"{coop['regularGrade']['name']} {coop['regularGradePoint']}"
        boss_per_cnt = ''
        if card['defeatBossCount']:
            boss_per_cnt = f"({card['playCount'] / card['defeatBossCount']:.2f})"
        gdpc = ''
        dpc = ''
        rpc = ''
        ppc = ''
        if card['playCount']:
            gdpc = f"({card['goldenDeliverCount'] / card['playCount']:.2f})"
            dpc = f"({card['deliverCount'] / card['playCount']:.2f})"
            rpc = f"({card['rescueCount'] / card['playCount']:.2f})"
            ppc = f"({card['totalPoint'] / card['playCount']:.2f})"
        coop_msg = f"""&nbsp; | {name}
现有点数 | {card['regularPoint']}
打工次数 | {card['playCount']}
金鲑鱼卵 | {card['goldenDeliverCount']} {gdpc}
鲑鱼卵 | {card['deliverCount']} {dpc}
头目鲑鱼 | {card['defeatBossCount']} {boss_per_cnt}
救援次数 | {card['rescueCount']} {rpc}
累计点数 | {card['totalPoint']} {ppc}
鳞片 | 🥉{p['bronze']} 🥈{p['silver']} 🏅️{p['gold']}"""
        if from_group:
            coop_msg = f"""打工次数 | {card['playCount']}
头目鲑鱼 | {card['defeatBossCount']} {boss_per_cnt}"""

    ar = (history.get('xMatchMaxAr') or {}).get('power') or 0
    lf = (history.get('xMatchMaxLf') or {}).get('power') or 0
    gl = (history.get('xMatchMaxGl') or {}).get('power') or 0
    cl = (history.get('xMatchMaxCl') or {}).get('power') or 0
    x_msg = '||'
    if any([ar, lf, gl, cl]) and not from_group:
        x_msg = f"X | {ar:>7.2f}, {lf:>7.2f}, {gl:>7.2f}, {cl:>7.2f}\n||"

    _league = ''
    _open = ''
    if history.get('leagueMatchPlayHistory'):
        _l = history['leagueMatchPlayHistory']
        _n = _l['attend'] - _l['gold'] - _l['silver'] - _l['bronze']
        _league = f"🏅️{_l['gold']:>3} 🥈{_l['silver']:>3} 🥉{_l['bronze']:>3} &nbsp; {_n:>3} ({_l['attend']})"
    if history.get('bankaraMatchOpenPlayHistory'):
        _o = history['bankaraMatchOpenPlayHistory']
        _n = _o['attend'] - _o['gold'] - _o['silver'] - _o['bronze']
        _open = f"🏅️{_o['gold']:>3} 🥈{_o['silver']:>3} 🥉{_o['bronze']:>3} &nbsp; {_n:>3} ({_o['attend']})"

    player_name = player['name'].replace('`', '&#96;').replace('|', '&#124;')
    msg = f"""####
|||
|---:|---|
&nbsp; |{player_name} #{player['nameId']}
&nbsp; |{player['byname']}
等级 | {history['rank']}
技术 | {history['udemae']}
最高技术 | {history['udemaeMax']}
总胜利数 | {history['winCountTotal']}{all_cnt} {r}
涂墨面积 | {history['paintPointTotal']:,}p
徽章 | {len(history['badges'])}
活动 | {_league}
开放 | {_open}
首次游玩 | {s_time:%Y-%m-%d %H:%M:%S} +08:00
当前时间 | {c_time:%Y-%m-%d %H:%M:%S} +08:00
{x_msg}
{coop_msg}
|||
"""
    return msg
