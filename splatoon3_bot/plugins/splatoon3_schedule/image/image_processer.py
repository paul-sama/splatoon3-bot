from ..data import get_festivals_data
from .image_processer_tools import *
from ..utils import *


def get_festival(festivals):
    """绘制 祭典地图"""
    festival = festivals[0]
    flag_festival_close = False
    # 判断祭典是否结束
    if festival["state"] == "CLOSED":
        flag_festival_close = True
    # 获取翻译
    _id = festival["__splatoon3ink_id"]
    festival_data = get_trans_cht_data()["festivals"]
    trans_cht_festival_data = festival_data.get(_id)
    # 替换为翻译
    teams_list = []
    if trans_cht_festival_data is not None:
        # 有中文翻译源
        festival["title"] = trans_cht_festival_data.get("title", festival["title"])
        for v in range(3):
            festival["teams"][v]["teamName"] = trans_cht_festival_data["teams"][v].get(
                "teamName", festival["teams"][v]["teamName"]
            )
            teams_list.append(festival["teams"][v])
    else:
        # 没有中文翻译源
        for v in range(3):
            teams_list.append(festival["teams"][v])

    # 开始绘图
    image_background_size = (1100, 700)
    if flag_festival_close:
        image_background_size = (1100, 1400)
    card_size = (1040, 660)
    # 取背景rgb颜色
    bg_rgb = dict_bg_rgb["祭典"]
    # 创建纯色背景
    image_background = Image.new("RGBA", image_background_size, bg_rgb)
    bg_mask = get_file("festival_mask").resize((600, 400))
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)
    # 圆角化
    image_background = circle_corner(image_background, radii=16)

    # 绘制组别卡片
    pos_h = 20
    team_card = get_festival_team_card(festival, card_size, teams_list, font_path=ttf_path_jp)
    team_card_pos = ((image_background_size[0] - card_size[0]) // 2, pos_h)
    paste_with_a(image_background, team_card, team_card_pos)
    pos_h += card_size[1] + 20
    if flag_festival_close:
        # 绘制结算卡片
        result_card = get_festival_result_card(card_size, teams_list, font_path=ttf_path_jp)
        result_card_pos = ((image_background_size[0] - card_size[0]) // 2, pos_h)
        paste_with_a(image_background, result_card, result_card_pos)

    return image_background


def get_events(events):
    """绘制 活动地图"""
    # 计算全部活动的举办次数来计算图片高度
    times = 0
    for index, event in enumerate(events):
        times += len(event["timePeriods"])
    background_size = (1084, (440 + 75 * times) * len(events))
    # 取背景rgb颜色
    bg_rgb = dict_bg_rgb["活动"]
    # 创建纯色背景
    image_background = Image.new("RGBA", background_size, bg_rgb)
    bg_mask = get_file("cat_paw_mask").resize((400, 250))
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)
    # 圆角
    image_background = circle_corner(image_background, radii=20)
    # 遍历每个活动
    pos_h = 0
    for index, event in enumerate(events):
        event_card_bg_size = (background_size[0] - 40, 420 + 75 * len(event["timePeriods"]))  # 75高度为每个时间段卡片占用的高度
        # 获取翻译
        cht_event_data = event["leagueMatchSetting"]["leagueMatchEvent"]
        _id = cht_event_data["id"]
        trans_cht_event_data = get_trans_cht_data()["events"][_id]
        # 替换为翻译文本
        cht_event_data["name"] = trans_cht_event_data.get("name", cht_event_data["name"])
        cht_event_data["desc"] = trans_cht_event_data.get("desc", cht_event_data["desc"])
        cht_event_data["regulation"] = trans_cht_event_data.get("regulation", cht_event_data["regulation"])

        # 顶部活动标志(大号)
        pos_h += 20
        game_mode_img_size = (80, 80)
        game_mode_img = get_file("event_bg").resize(game_mode_img_size, Image.ANTIALIAS)
        game_mode_img_pos = (20, pos_h)
        paste_with_a(image_background, game_mode_img, game_mode_img_pos)
        pos_h += game_mode_img_size[1] + 20
        # 绘制主标题
        main_title = cht_event_data["name"]
        drawer = ImageDraw.Draw(image_background)
        ttf = ImageFont.truetype(ttf_path_chinese, 40)
        main_title_pos = (game_mode_img_pos[0] + game_mode_img_size[0] + 20, game_mode_img_pos[1])
        main_title_size = ttf.getsize(main_title)
        drawer.text(main_title_pos, main_title, font=ttf, fill=(255, 255, 255))
        # 绘制描述
        desc = cht_event_data["desc"]
        ttf = ImageFont.truetype(ttf_path_chinese, 30)
        desc_pos = (main_title_pos[0], main_title_pos[1] + main_title_size[1] + 10)
        drawer.text(desc_pos, desc, font=ttf, fill=(255, 255, 255))
        # 绘制对战卡片
        # 全问号活动会导致地图和时间参数错误，这里改用try except
        try:
            event_card = get_event_card(event, event_card_bg_size)
        except Exception:
            error = "傻逼任天堂又整不出新活，开始输出问号活动了，活动地图渲染失败"
            logger.error(error)
            drawer.text((desc_pos[0], desc_pos[1] + 50), error, font=ttf, fill=(255, 255, 255))
            pos_h += 100
            continue
        event_card_pos = (20, pos_h + 20)
        paste_with_a(image_background, event_card, event_card_pos)
        pos_h += event_card.size[1] + 30
        # 绘制祭典说明卡片
        event_desc_card_bg_size = (event_card_bg_size[0], 300)
        event_desc_card = get_event_desc_card(cht_event_data, event_desc_card_bg_size)
        event_card_pos = (20, pos_h)
        paste_with_a(image_background, event_desc_card, event_card_pos)
        pos_h += event_desc_card_bg_size[1]
        # 计算下一行高度
        pos_h += 20
    return image_background


def get_stages(schedule, num_list, contest_match=None, rule_match=None):
    """绘制 竞赛地图"""
    # 涂地
    regular = schedule["regularSchedules"]["nodes"]
    # 真格
    ranked = schedule["bankaraSchedules"]["nodes"]
    # X段
    xschedule = schedule["xSchedules"]["nodes"]
    # 祭典
    festivals = schedule["festSchedules"]["nodes"]

    # 如果存在祭典，且当前时间位于祭典，转变为输出祭典地图，后续不再进行处理
    if have_festival(festivals) and now_is_festival(festivals):
        festivals = get_festivals_data()["JP"]["data"]["festRecords"]["nodes"]
        image = get_festival(festivals)
        return image

    cnt = 0
    time_head_count = 0
    # 计算满足条件的有效数据有多少排
    for i in num_list:
        # 筛选到数据的个数
        count_match_data = 0
        if contest_match is None or contest_match == "Turf War":
            if regular[i]["regularMatchSetting"] is not None:
                if rule_match is None:
                    cnt += 1
                    count_match_data += 1
        if contest_match is None or contest_match == "Ranked Challenge":
            if ranked[i]["bankaraMatchSettings"] is not None:
                if rule_match is None or rule_match == ranked[i]["bankaraMatchSettings"][0]["vsRule"]["rule"]:
                    cnt += 1
                    count_match_data += 1
        if contest_match is None or contest_match == "Ranked Open":
            if ranked[i]["bankaraMatchSettings"] is not None:
                if rule_match is None or rule_match == ranked[i]["bankaraMatchSettings"][1]["vsRule"]["rule"]:
                    cnt += 1
                    count_match_data += 1

        if contest_match is None or contest_match == "X Schedule":
            if xschedule[i]["xMatchSetting"] is not None:
                if rule_match is None or rule_match == xschedule[i]["xMatchSetting"]["vsRule"]["rule"]:
                    cnt += 1
                    count_match_data += 1

        # 如果有筛选结果,需要加上一个时间卡片
        if count_match_data:
            time_head_count += 1

    if cnt == 0 and not have_festival(festivals):
        # 没有搜索结果情况下，用全部list再次调用自身
        num_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        return get_stages(schedule, num_list, contest_match, rule_match)

    time_head_bg_size = (540, 60)
    # 一张对战卡片高度为340 时间卡片高度为time_head_bg_size[1] 加上间隔为10
    background_size = (1044, 340 * cnt + (time_head_bg_size[1] + 10) * time_head_count)
    # 取背景rgb颜色
    default_bg_rgb = dict_bg_rgb["X Schedule"]
    if contest_match is not None:
        bg_rgb = dict_bg_rgb[contest_match]
    else:
        bg_rgb = default_bg_rgb
    # 创建纯色背景
    image_background = Image.new("RGBA", background_size, bg_rgb)
    bg_mask = get_file("fight_mask").resize((600, 399))
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)

    total_pos = 0
    for i in num_list:
        pos = 0
        # 创建一张纯透明图片 用来存放一个时间周期内的多张地图卡片
        background = Image.new("RGBA", background_size, (0, 0, 0, 0))
        # 筛选到数据的个数
        count_match_data = 0

        # 第一排绘制 默认为涂地模式
        if contest_match is None or contest_match == "Turf War":
            if regular[i]["regularMatchSetting"] is not None:
                if rule_match is None:
                    count_match_data += 1

                    stage = regular[i]["regularMatchSetting"]["vsStages"]
                    regular_card = get_stage_card(
                        ImageInfo(
                            name=stage[0]["name"],
                            url=stage[0]["image"]["url"],
                            zh_name=get_trans_stage(stage[0]["id"]),
                            source_type="对战地图",
                        ),
                        ImageInfo(
                            name=stage[1]["name"],
                            url=stage[1]["image"]["url"],
                            zh_name=get_trans_stage(stage[1]["id"]),
                            source_type="对战地图",
                        ),
                        "一般比赛",
                        "Regular",
                        regular[i]["regularMatchSetting"]["vsRule"]["rule"],
                        time_converter_hm(regular[i]["startTime"]),
                        time_converter_hm(regular[i]["endTime"]),
                    )
                    paste_with_a(background, regular_card, (10, pos))
                    pos += 340
                    total_pos += 340

        # 第二排绘制 默认为真格区域
        if contest_match is None or contest_match == "Ranked Challenge":
            if ranked[i]["bankaraMatchSettings"] is not None:
                if rule_match is None or rule_match == ranked[i]["bankaraMatchSettings"][0]["vsRule"]["rule"]:
                    count_match_data += 1
                    stage = ranked[i]["bankaraMatchSettings"][0]["vsStages"]
                    ranked_challenge_card = get_stage_card(
                        ImageInfo(
                            name=stage[0]["name"],
                            url=stage[0]["image"]["url"],
                            zh_name=get_trans_stage(stage[0]["id"]),
                            source_type="对战地图",
                        ),
                        ImageInfo(
                            name=stage[1]["name"],
                            url=stage[1]["image"]["url"],
                            zh_name=get_trans_stage(stage[1]["id"]),
                            source_type="对战地图",
                        ),
                        "蛮颓比赛-挑战",
                        "Ranked-Challenge",
                        ranked[i]["bankaraMatchSettings"][0]["vsRule"]["rule"],
                        time_converter_hm(ranked[i]["startTime"]),
                        time_converter_hm(ranked[i]["endTime"]),
                    )
                    paste_with_a(background, ranked_challenge_card, (10, pos))
                    pos += 340
                    total_pos += 340

        # 第三排绘制 默认为真格开放
        if contest_match is None or contest_match == "Ranked Open":
            if ranked[i]["bankaraMatchSettings"] is not None:
                if rule_match is None or rule_match == ranked[i]["bankaraMatchSettings"][1]["vsRule"]["rule"]:
                    count_match_data += 1
                    stage = ranked[i]["bankaraMatchSettings"][1]["vsStages"]
                    ranked_challenge_card = get_stage_card(
                        ImageInfo(
                            name=stage[0]["name"],
                            url=stage[0]["image"]["url"],
                            zh_name=get_trans_stage(stage[0]["id"]),
                            source_type="对战地图",
                        ),
                        ImageInfo(
                            name=stage[1]["name"],
                            url=stage[1]["image"]["url"],
                            zh_name=get_trans_stage(stage[1]["id"]),
                            source_type="对战地图",
                        ),
                        "蛮颓比赛-开放",
                        "Ranked-Open",
                        ranked[i]["bankaraMatchSettings"][1]["vsRule"]["rule"],
                        time_converter_hm(ranked[i]["startTime"]),
                        time_converter_hm(ranked[i]["endTime"]),
                    )
                    paste_with_a(background, ranked_challenge_card, (10, pos))
                    pos += 340
                    total_pos += 340

        # 第四排绘制 默认为X赛
        if contest_match is None or contest_match == "X Schedule":
            if xschedule[i]["xMatchSetting"] is not None:
                if rule_match is None or rule_match == xschedule[i]["xMatchSetting"]["vsRule"]["rule"]:
                    count_match_data += 1
                    stage = xschedule[i]["xMatchSetting"]["vsStages"]
                    ranked_challenge_card = get_stage_card(
                        ImageInfo(
                            name=stage[0]["name"],
                            url=stage[0]["image"]["url"],
                            zh_name=get_trans_stage(stage[0]["id"]),
                            source_type="对战地图",
                        ),
                        ImageInfo(
                            name=stage[1]["name"],
                            url=stage[1]["image"]["url"],
                            zh_name=get_trans_stage(stage[1]["id"]),
                            source_type="对战地图",
                        ),
                        "X比赛",
                        "X",
                        xschedule[i]["xMatchSetting"]["vsRule"]["rule"],
                        time_converter_hm(xschedule[i]["startTime"]),
                        time_converter_hm(xschedule[i]["endTime"]),
                    )
                    paste_with_a(background, ranked_challenge_card, (10, pos))
                    pos += 340
                    total_pos += 340
        # 如果有筛选结果，将时间表头贴到底图上
        if count_match_data:
            # 取涂地模式的时间，除举办祭典外，都可用
            date_time = time_converter_yd(regular[i]["startTime"])
            start_time = time_converter_hm(regular[i]["startTime"])
            end_time = time_converter_hm(regular[i]["endTime"])
            # 绘制时间表头
            time_head_bg = get_time_head_bg(time_head_bg_size, date_time, start_time, end_time)
            # 贴到大图上
            time_head_bg_pos = (
                (background_size[0] - time_head_bg_size[0]) // 2,
                total_pos - 340 * count_match_data + 10,
            )
            paste_with_a(image_background, time_head_bg, time_head_bg_pos)
            total_pos += time_head_bg_size[1] + 10

            # 将一组图片贴到底图上
            paste_with_a(
                image_background,
                background,
                (0, time_head_bg_pos[1] + time_head_bg_size[1]),
            )

    # 圆角化
    image_background = circle_corner(image_background, radii=16)
    return image_background


def get_coop_stages(stage, weapon, time, boss, mode):
    """绘制 打工地图"""

    # 校验是否需要绘制小鲑鱼(现在时间处于该打工时间段内)
    def check_coop_fish(_time):
        start_time = _time.split(" - ")[0]
        now_time = get_time_now_china()
        # 输入时间都缺少年份，需要手动补充一个年份后还原为date对象
        year = now_time.year
        start_time = str(year) + "-" + start_time
        st = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        if st < now_time:
            return True
        return False

    top_size_pos = (0, -2)
    bg_size = (800, len(stage) * 162 + top_size_pos[1])
    stage_bg_size = (300, 160)
    weapon_size = (90, 90)
    boss_size = (40, 40)
    mode_size = (40, 40)
    coop_fish_size = (36, 48)

    # 创建纯色背景
    image_background_rgb = dict_bg_rgb["打工"]
    image_background = Image.new("RGBA", bg_size, image_background_rgb)
    bg_mask_size = (300, 200)
    bg_mask = get_file("coop_mask").resize(bg_mask_size)
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)

    # 绘制地图信息
    coop_stage_bg = Image.new("RGBA", (bg_size[0], bg_size[1] + 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(coop_stage_bg)
    font = ImageFont.truetype(ttf_path, 30)
    for pos, val in enumerate(time):
        # 绘制时间文字
        time_text_pos = (50, 5 + pos * 160)
        time_text_size = font.getsize(val)
        dr.text(time_text_pos, val, font=font, fill="#FFFFFF")
        if check_coop_fish(val):
            # 现在时间处于打工时间段内，绘制小鲑鱼
            coop_fish_img = get_file("coop_fish").resize(coop_fish_size)
            coop_fish_img_pos = (5, 8 + pos * 160)
            paste_with_a(coop_stage_bg, coop_fish_img, coop_fish_img_pos)
    for pos, val in enumerate(stage):
        # 绘制打工地图
        stage_bg = get_save_file(val).resize(stage_bg_size, Image.ANTIALIAS)
        stage_bg_pos = (500, 2 + 162 * pos)
        coop_stage_bg.paste(stage_bg, stage_bg_pos)

        # 绘制 地图名
        stage_name_bg = get_stage_name_bg(val.zh_name, 25)
        stage_name_bg_size = stage_name_bg.size
        # X:地图x点位+一半的地图宽度-文字背景的一半宽度   Y:地图Y点位+一半地图高度-文字背景高度
        stage_name_bg_pos = (
            stage_bg_pos[0] + +stage_bg_size[0] // 2 - stage_name_bg_size[0] // 2,
            stage_bg_pos[1] + stage_bg_size[1] - stage_name_bg_size[1],
        )
        paste_with_a(coop_stage_bg, stage_name_bg, stage_name_bg_pos)

        for pos_weapon, val_weapon in enumerate(weapon[pos]):
            # 绘制武器底图
            weapon_bg_img = Image.new("RGBA", weapon_size, (30, 30, 30))
            # 绘制武器图片
            weapon_image = get_save_file(val_weapon).resize(weapon_size, Image.ANTIALIAS)
            paste_with_a(weapon_bg_img, weapon_image, (0, 0))
            coop_stage_bg.paste(weapon_bg_img, (120 * pos_weapon + 20, 60 + 160 * pos))
    for pos, val in enumerate(boss):
        if val != "":
            # 绘制boss图标
            boss_img = get_file(val).resize(boss_size)
            boss_img_pos = (500, 160 * pos + stage_bg_size[1] - 40)
            paste_with_a(coop_stage_bg, boss_img, boss_img_pos)
    for pos, val in enumerate(mode):
        # 绘制打工模式图标
        mode_img = get_file(val).resize(mode_size)
        mode_img_pos = (500 - 70, 160 * pos + 15)
        paste_with_a(coop_stage_bg, mode_img, mode_img_pos)

    paste_with_a(image_background, coop_stage_bg, top_size_pos)
    # 圆角
    image_background = circle_corner(image_background, radii=20)

    return image_background


def get_random_weapon(weapon1: [WeaponData], weapon2: [WeaponData]):
    """绘制 随机武器"""
    # 底图
    image_background_size = (660, 500)
    image_background = circle_corner(get_file("bg2").resize(image_background_size), radii=20)
    # 绘制上下两块武器区域
    weapon_card_bg_size = (image_background_size[0] - 10, (image_background_size[1] - 10) // 2)
    top_weapon_card = get_weapon_card(weapon1, weapon_card_bg_size, dict_bg_rgb["上-武器卡片"], (34, 34, 34))
    down_weapon_card = get_weapon_card(weapon2, weapon_card_bg_size, dict_bg_rgb["下-武器卡片"], (255, 255, 255))
    # 将武器区域贴到最下层背景
    paste_with_a(image_background, top_weapon_card, (5, 5))
    paste_with_a(image_background, down_weapon_card, (5, (image_background_size[1]) // 2))
    # 绘制私房图标
    private_img_size = (35, 35)
    private_img_pos = (
        (image_background_size[0] - private_img_size[0]) // 2,
        (image_background_size[1] - private_img_size[1]) // 2,
    )
    private_img = get_file("private").resize(private_img_size)
    paste_with_a(image_background, private_img, private_img_pos)

    return image_background


def get_help():
    """绘制 帮助图片"""
    image_background_size = (1200, 2200)
    if plugin_config.splatoon3_schedule_plugin_priority_mode:
        image_background_size = (1200, 2500)
    # 取背景rgb颜色
    bg_rgb = dict_bg_rgb["活动"]
    # 创建纯色背景
    image_background = Image.new("RGBA", image_background_size, bg_rgb)
    bg_mask = get_file("cat_paw_mask").resize((400, 250))
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)
    # 圆角
    image_background = circle_corner(image_background, radii=20)
    # 绘制标题
    font_size = 30
    text_bg = get_translucent_name_bg("帮助手册", 80, font_size)
    text_bg_size = text_bg.size
    # 贴上文字背景
    text_bg_pos = ((image_background_size[0] - text_bg_size[0]) // 2, 20)
    paste_with_a(image_background, text_bg, text_bg_pos)
    # 初始化一些参数
    drawer = ImageDraw.Draw(image_background)
    text_width = 800
    height = text_bg_pos[1] + text_bg_size[1] + 20
    title_rgb = dict_bg_rgb["祭典时间-金黄"]

    # 绘制title
    title = "对战地图 查询"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h
    # 绘制 帮助卡片 对战地图查询
    pre = "查询指令:"
    order_list = ["/图", "/图图", "/下图", "/下下图", "/全部图"]
    desc_list = ["查询当前或指定时段 所有模式 的地图", "前面如果是 全部 则显示至多未来5个时段的地图"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h
    # 绘制 帮助卡片 对战地图查询
    pre = "指定时间段查询:"
    order_list = ["/0图", "/123图", "/1图", "/2468图"]
    desc_list = ["可以在前面加上多个0-9的数字，不同数字代表不同时段", "如0代表当前，1代表下时段，2代表下下时段，以此类推"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h + 10

    # 绘制title
    title = "对战地图 筛选查询"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h
    # 绘制 帮助卡片 对战地图查询
    pre = "查询指令:"
    order_list = ["/挑战", "/涂地", "/x赛", "/塔楼", "/开放挑战", "/pp抢鱼"]
    desc_list = ["支持指定规则或比赛，或同时指定规则比赛", "触发词进行了语义化处理，很多常用的称呼也能触发，如:pp和排排 都等同于 开放;抢鱼对应鱼虎;涂涂对应涂地 等"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h
    # 绘制 帮助卡片 对战地图查询
    pre = "指定时间段查询:"
    order_list = ["/0挑战", "/1234开放塔楼", "/全部x赛区域"]
    desc_list = ["与图图的指定时间段查询方法一致，如果指定时间段没有匹配的结果，会返回全部时间段满足该筛选的结果", "前面加上 全部 则显示未来24h满足条件的对战"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    # 绘制title
    title = "打工 查询"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h
    # 绘制 帮助卡片 对战地图查询
    pre = "查询指令:"
    order_list = ["/工", "/打工", "/bigrun", "/团队打工", "/全部工"]
    desc_list = ["查询当前和下一时段的打工地图，如果存在bigrun或团队打工时，也会显示在里面，并根据时间自动排序", "前面加上 全部 则显示接下来的五场打工地图"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    # 绘制title
    title = "其他 查询"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h
    # 绘制 帮助卡片 对战地图查询
    pre = "查询指令:"
    order_list = ["/祭典", "/活动", "/帮助", "/help"]
    desc_list = ["查询 祭典  活动 ", "帮助/help:回复本帮助图片"]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    # 绘制title
    title = "私房用 随机武器"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h
    # 绘制 帮助卡片 对战地图查询
    pre = "查询指令:"
    order_list = ["/随机武器", "/随机武器 nice弹", "/随机武器 小枪 刷 狙 泡"]
    desc_list = [
        "可以在 随机武器 后面，接至多四个参数，每个参数间用空格分开",
        "参数包括全部的 武器类型，如 小枪 双枪 弓 狙 等;全部的 副武器名称，如 三角雷 水球 雨帘;全部的大招名称，如 nice弹 龙卷风 rpg等",
        "如果不带参数或参数小于4，剩下的会自动用 同一大类下的武器 进行筛选，如 狙 和 加特林 都属于 远程类，小枪 与 刷子，滚筒 等属于 近程类，保证尽可能公平",
        "如果不希望进行任何限制，也可以发送 /随机武器完全随机，来触发不加限制的真随机武器(平衡性就没法保证了)",
    ]
    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    if plugin_config.splatoon3_schedule_plugin_priority_mode:
        # 添加nso插件的帮助菜单

        # 绘制title
        title = "nso相关指令"
        title_pos = (20, height)
        w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
        height += h
        # 绘制 帮助卡片 对战地图查询
        pre = "指令:"
        order_list = ["/login", "/last", "/friends", "/report", "/me"]
        desc_list = [
            "/login：绑定nso账号，后续指令都是需要完成绑定后才可以使用，Q群使用请先加入下面联系方式里的 kook频道",
            "/last：查询上一局比赛或打工的数据",
            "/friends：显示在线的ns好友",
            "/report：获取昨天或指定日期的日报数据(胜场，游戏局数，金银铜牌，打工鳞片等数量变化)，支持指定日期，如 /report 2023-12-17",
            "/me：获取自己个人数据(总场数，胜率，金银铜牌数量等)",
        ]
        text_card, card_h = drawer_help_card(pre, order_list, desc_list)
        # 贴图
        text_bg_pos = (title_pos[0] + 30, height)
        paste_with_a(image_background, text_card, text_bg_pos)
        height += card_h

    # # 绘制title
    # title = "频道主命令"
    # title_pos = (20, height)
    # w, h = drawer_text(drawer, title, title_pos, text_width, (255, 167, 137))
    # height += h
    # # 绘制 帮助卡片 对战地图查询
    # pre = "指令:"
    # order_list = ["开启/关闭查询"]
    # desc_list = ["频道服务器拥有者可发送 关闭查询 来禁用该频道内bot的主动地图查询功能"]
    # text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # # 贴图
    # text_bg_pos = (title_pos[0] + 30, height)
    # paste_with_a(image_background, text_card, text_bg_pos)
    # height += card_h
    #
    # # 绘制title
    # title = "bot管理员命令"
    # title_pos = (20, height)
    # w, h = drawer_text(drawer, title, title_pos, text_width, (255, 167, 137))
    # height += h
    # # 绘制 帮助卡片 对战地图查询
    # pre = "指令:"
    # order_list = ["清空图片缓存", "更新武器数据", "开启/关闭查询", "开启/关闭推送"]
    # desc_list = [
    #     "清空图片缓存：会主动清空2h内的全部缓存图",
    #     "更新武器数据：主动更新武器数据库(新版本武器不一定有中文，还是需要定期更新本插件)",
    #     "开启/关闭查询：开关本频道的地图查询功能",
    #     "开启/关闭推送：开关本频道的地图推送功能(建议在除q频道，q群以外的渠道使用)",
    # ]
    # text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # # 贴图
    # text_bg_pos = (title_pos[0] + 30, height)
    # paste_with_a(image_background, text_card, text_bg_pos)
    # height += card_h

    # 绘制title
    title = "关于本插件"
    title_pos = (20, height)
    w, h = drawer_text(drawer, title, title_pos, text_width, title_rgb)
    height += h
    # 绘制 帮助卡片 对战地图查询
    pre = ""
    order_list = []
    desc_list = [
        "本插件已开源，地址如下：",
        "https://github.com/Cypas/splatoon3-schedule",
        "有github账号的人可以去帮忙点个star，这是对我们最大的支持了",
    ]

    if plugin_config.splatoon3_is_official_bot:
        desc_list.append("小鱿鱿官方联系方式: Kook服务器id：85644423 Q群：827977720")
    desc_list.append("插件作者:Cypas_Nya;Paul;Sky_miner")

    text_card, card_h = drawer_help_card(pre, order_list, desc_list)
    # 贴图
    text_bg_pos = (title_pos[0] + 30, height)
    paste_with_a(image_background, text_card, text_bg_pos)
    height += card_h

    return image_background
