import io
import os
import random
from io import BytesIO
import urllib3
from PIL import Image, ImageDraw, ImageFont
from nonebot.log import logger
from .translation import get_trans_stage, get_trans_game_mode
from .utils import *
from .image_db import ImageDB

# 根路径
cur_path = os.path.dirname(__file__)

# 图片文件夹
image_folder = os.path.join(cur_path, "staticData", "ImageData")
# 武器文件夹
weapon_folder = os.path.join(cur_path, "staticData", "weapon")
# 字体
ttf_path = os.path.join(cur_path, "staticData", "SplatoonFontFix.otf")
ttf_path_chinese = os.path.join(cur_path, "staticData", "Text.ttf")

http = urllib3.PoolManager()
imageDB = ImageDB()


# 图片转base64
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return buffered.getvalue()


# 取文件
def get_file(name, format_name="png"):
    img = Image.open(os.path.join(image_folder, "{}.{}".format(name, format_name)))
    return img


# 获取武器
def get_weapon(name):
    return Image.open(os.path.join(weapon_folder, "{}".format(name)))


# 网页读文件
def get_file_url(url):
    r = http.request("GET", url, timeout=5)
    return r.data


# 向数据库新增或读取素材图片二进制文件
def get_save_file(img: ImageInfo):
    res = imageDB.get_img_data(img.name)
    if not res:
        image_data = get_file_url(img.url)
        if len(image_data) != 0:
            logger.info("[ImageDB] new image {}".format(img.name))
            imageDB.add_or_modify_IMAGE_DATA(
                img.name, image_data, img.zh_name, img.source_type
            )
        return Image.open(io.BytesIO(image_data))
    else:
        return Image.open(io.BytesIO(res[0]))


# 取文件路径
def get_file_path(name, format_name="png"):
    return os.path.join(image_folder, "{}.{}".format(name, format_name))


# 圆角处理
def circle_corner(img, radii):
    """
    圆角处理
    :param img: 源图象。
    :param radii: 半径，如：30。
    :return: 返回一个圆角处理后的图象。
    """
    # 画圆（用于分离4个角）
    circle = Image.new("L", (radii * 2, radii * 2), 0)  # 创建一个黑色背景的画布
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 画白色圆形

    # 原图
    img = img.convert("RGBA")
    w, h = img.size

    # 画4个角（将整圆分离为4个部分）
    alpha = Image.new("L", img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))  # 右上角
    alpha.paste(
        circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii)
    )  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))  # 左下角

    img.putalpha(alpha)  # 白色区域透明可见，黑色区域不可见
    return alpha, img


# 图片 平铺填充
def tiled_fill(big_image, small_image):
    catImWidth, catImHeigh = big_image.size
    faceImWidth, faceImHeigh = small_image.size
    for left in range(0, catImWidth, faceImWidth):  # 横纵两个方向上用两个for循环实现平铺效果
        for top in range(0, catImHeigh, faceImHeigh):
            paste_with_a(big_image, small_image, (left, top))
    return big_image


# 图像粘贴 加上a通道参数 使圆角透明
def paste_with_a(image_background, image_pasted, pos):
    _, _, _, a = image_pasted.convert("RGBA").split()
    image_background.paste(image_pasted, pos, mask=a)


# 绘制 地图名称及文字底图
def get_stage_name_bg(stage_name, font_size=25):
    stage_name_bg_size = (len(stage_name * font_size) + 16, 30)
    # 新建画布
    stage_name_bg = Image.new("RGBA", stage_name_bg_size, (0, 0, 0))
    # 圆角化
    _, stage_name_bg = circle_corner(stage_name_bg, radii=16)
    # # 绘制文字
    drawer = ImageDraw.Draw(stage_name_bg)
    ttf = ImageFont.truetype(ttf_path_chinese, font_size)
    # 文字居中绘制
    w, h = ttf.getsize(stage_name)
    text_pos = ((stage_name_bg_size[0] - w) // 2, (stage_name_bg_size[1] - h) // 2)
    drawer.text(text_pos, stage_name, font=ttf, fill=(255, 255, 255))
    return stage_name_bg


# 绘制 时间表头
def get_time_head_bg(time_head_bg_size, date_time, start_time, end_time):
    # 绘制背景
    time_head_bg = get_file("时间表头").resize(time_head_bg_size)
    # 绘制开始，结束时间 文字居中绘制
    ttf = ImageFont.truetype(ttf_path, 40)
    time_head_text = "{}  {} - {}".format(date_time, start_time, end_time)
    w, h = ttf.getsize(time_head_text)
    time_head_text_pos = (
        (time_head_bg_size[0] - w) // 2,
        (time_head_bg_size[1] - h) // 2 - 12,
    )
    drawer = ImageDraw.Draw(time_head_bg)
    drawer.text(time_head_text_pos, time_head_text, font=ttf, fill=(255, 255))
    return time_head_bg


# 绘制 一排 地图卡片
def get_stage_card(
    stage1,
    stage2,
    contest_mode,
    contest_name,
    game_mode,
    start_time,
    end_time,
    img_size=(1024, 340),
):
    _, image_background = circle_corner(get_file("背景").resize(img_size), radii=20)

    ## 绘制两张地图
    # 计算尺寸，加载图片
    stage_size = (int(img_size[0] * 0.48), int(img_size[1] * 0.7))
    image_left = get_save_file(stage1).resize(stage_size, Image.ANTIALIAS)
    image_right = get_save_file(stage2).resize(stage_size, Image.ANTIALIAS)
    # 定义圆角 蒙版
    _, image_alpha = circle_corner(image_left, radii=16)

    # 计算地图间隔
    width_between_stages = int((img_size[0] - 2 * stage_size[0]) / 3)
    # 绘制第一张地图
    # 图片左上点位
    start_stage_pos = (
        width_between_stages,
        int((img_size[1] - stage_size[1]) / 8 * 7) - 20,
    )
    image_background.paste(image_left, start_stage_pos, mask=image_alpha)
    # 绘制第二张地图
    # 图片左上点位
    next_stage_pos = (
        start_stage_pos[0] + width_between_stages + stage_size[0],
        start_stage_pos[1],
    )
    image_background.paste(image_right, next_stage_pos, mask=image_alpha)

    ## 绘制地图中文名及文字背景
    # 左半地图名
    stage_name_bg = get_stage_name_bg(stage1.zh_name, 30)
    stage_name_bg_size = stage_name_bg.size
    # X:地图x点位+一半的地图宽度-文字背景的一半宽度   Y:地图Y点位+一半地图高度-文字背景高度
    stage_name_bg_pos = (
        start_stage_pos[0] + stage_size[0] // 2 - stage_name_bg_size[0] // 2,
        start_stage_pos[1] + stage_size[1] - stage_name_bg_size[1],
    )
    paste_with_a(image_background, stage_name_bg, stage_name_bg_pos)

    # 右半地图名
    stage_name_bg = get_stage_name_bg(stage2.zh_name, 30)
    stage_name_bg_size = stage_name_bg.size
    # X:地图x点位+一半的地图宽度-文字背景的一半宽度   Y:地图Y点位+一半地图高度-文字背景高度
    stage_name_bg_pos = (
        next_stage_pos[0] + +stage_size[0] // 2 - stage_name_bg_size[0] // 2,
        next_stage_pos[1] + stage_size[1] - stage_name_bg_size[1],
    )
    paste_with_a(image_background, stage_name_bg, stage_name_bg_pos)

    # 中间绘制 模式图标
    image_icon = get_file(contest_name)
    image_icon_size = image_icon.size
    # X: 整张卡片宽度/2 - 图标宽度/2    Y: 左地图x点位+地图高度/2 - 图标高度/2
    stage_mid_pos = (
        img_size[0] // 2 - image_icon_size[0] // 2,
        start_stage_pos[1] + stage_size[1] // 2 - image_icon_size[1] // 2,
    )
    paste_with_a(image_background, image_icon, stage_mid_pos)

    ## 绘制模式文本
    # 空白尺寸
    blank_size = (img_size[0], start_stage_pos[1])
    drawer = ImageDraw.Draw(image_background)
    # 绘制竞赛模式文字
    ttf = ImageFont.truetype(ttf_path_chinese, 40)
    contest_mode_pos = (start_stage_pos[0] + 10, start_stage_pos[1] - 60)
    drawer.text(contest_mode_pos, contest_mode, font=ttf, fill=(255, 255, 255))
    # 绘制游戏模式文字
    game_mode_text = get_trans_game_mode(game_mode)
    game_mode_text_pos = (blank_size[0] // 3, contest_mode_pos[1])
    drawer.text(game_mode_text_pos, game_mode_text, font=ttf, fill=(255, 255, 255))
    # 绘制游戏模式小图标
    game_mode_img = get_file(game_mode_text).resize((35, 35), Image.ANTIALIAS)
    game_mode_img_pos = (game_mode_text_pos[0] - 40, game_mode_text_pos[1] + 10)
    paste_with_a(image_background, game_mode_img, game_mode_img_pos)
    # # 绘制开始，结束时间
    # ttf = ImageFont.truetype(ttf_path, 40)
    # time_pos = (blank_size[0] * 2 // 3, contest_mode_pos[1] - 10)
    # drawer.text(
    #     time_pos, "{} - {}".format(start_time, end_time), font=ttf, fill=(255, 255, 255)
    # )

    return image_background


# 绘制 竞赛地图
def get_stages(schedule, num_list, contest_match=None, rule_match=None):
    # 涂地
    regular = schedule["regularSchedules"]["nodes"]
    # 真格
    ranked = schedule["bankaraSchedules"]["nodes"]
    # league = schedule['leagueSchedules']['nodes']
    # X段
    xschedule = schedule["xSchedules"]["nodes"]
    cnt = 0
    time_head_count = 0
    # 计算满足条件的有效数据有多少排
    for idx in num_list:
        # 筛选到数据的个数
        count_match_data = 0
        if contest_match is None or contest_match == "Turf War":
            if rule_match is None:
                cnt += 1
                count_match_data += 1
        if contest_match is None or contest_match == "Ranked Challenge":
            if (
                rule_match is None
                or rule_match
                == ranked[idx]["bankaraMatchSettings"][0]["vsRule"]["rule"]
            ):
                cnt += 1
                count_match_data += 1
        if contest_match is None or contest_match == "Ranked Open":
            if (
                rule_match is None
                or rule_match
                == ranked[idx]["bankaraMatchSettings"][1]["vsRule"]["rule"]
            ):
                cnt += 1
                count_match_data += 1

        if contest_match is None or contest_match == "X Schedule":
            if (
                rule_match is None
                or rule_match == xschedule[idx]["xMatchSetting"]["vsRule"]["rule"]
            ):
                cnt += 1
                count_match_data += 1

        # 如果有筛选结果,需要加上一个时间卡片
        if count_match_data:
            time_head_count += 1

    if cnt == 0:
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
    bg_mask = get_file("对战蒙版").resize((600, 399))
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)

    total_pos = 0
    for idx in num_list:
        pos = 0
        # 创建一张纯透明图片 用来存放一个时间周期内的多张地图卡片
        background = Image.new("RGBA", background_size, (0, 0, 0, 0))
        # 筛选到数据的个数
        count_match_data = 0

        # 第一排绘制 默认为涂地模式
        if contest_match is None or contest_match == "Turf War":
            if rule_match is None:
                count_match_data += 1

                stage = regular[idx]["regularMatchSetting"]["vsStages"]
                regular_card = get_stage_card(
                    ImageInfo(
                        stage[0]["name"],
                        stage[0]["image"]["url"],
                        get_trans_stage(stage[0]["id"]),
                        "对战地图",
                    ),
                    ImageInfo(
                        stage[1]["name"],
                        stage[1]["image"]["url"],
                        get_trans_stage(stage[1]["id"]),
                        "对战地图",
                    ),
                    "一般比赛",
                    "Regular",
                    regular[idx]["regularMatchSetting"]["vsRule"]["rule"],
                    time_converter(regular[idx]["startTime"]),
                    time_converter(regular[idx]["endTime"]),
                )
                paste_with_a(background, regular_card, (10, pos))
                pos += 340
                total_pos += 340

        # 第二排绘制 默认为真格区域
        if contest_match is None or contest_match == "Ranked Challenge":
            if (
                rule_match is None
                or rule_match
                == ranked[idx]["bankaraMatchSettings"][0]["vsRule"]["rule"]
            ):
                count_match_data += 1
                stage = ranked[idx]["bankaraMatchSettings"][0]["vsStages"]
                ranked_challenge_card = get_stage_card(
                    ImageInfo(
                        stage[0]["name"],
                        stage[0]["image"]["url"],
                        get_trans_stage(stage[0]["id"]),
                        "对战地图",
                    ),
                    ImageInfo(
                        stage[1]["name"],
                        stage[1]["image"]["url"],
                        get_trans_stage(stage[1]["id"]),
                        "对战地图",
                    ),
                    "蛮颓比赛-挑战",
                    "Ranked-Challenge",
                    ranked[idx]["bankaraMatchSettings"][0]["vsRule"]["rule"],
                    time_converter(ranked[idx]["startTime"]),
                    time_converter(ranked[idx]["endTime"]),
                )
                paste_with_a(background, ranked_challenge_card, (10, pos))
                pos += 340
                total_pos += 340

        # 第三排绘制 默认为真格开放
        if contest_match is None or contest_match == "Ranked Open":
            if (
                rule_match is None
                or rule_match
                == ranked[idx]["bankaraMatchSettings"][1]["vsRule"]["rule"]
            ):
                count_match_data += 1
                stage = ranked[idx]["bankaraMatchSettings"][1]["vsStages"]
                ranked_challenge_card = get_stage_card(
                    ImageInfo(
                        stage[0]["name"],
                        stage[0]["image"]["url"],
                        get_trans_stage(stage[0]["id"]),
                        "对战地图",
                    ),
                    ImageInfo(
                        stage[1]["name"],
                        stage[1]["image"]["url"],
                        get_trans_stage(stage[1]["id"]),
                        "对战地图",
                    ),
                    "蛮颓比赛-开放",
                    "Ranked-Open",
                    ranked[idx]["bankaraMatchSettings"][1]["vsRule"]["rule"],
                    time_converter(ranked[idx]["startTime"]),
                    time_converter(ranked[idx]["endTime"]),
                )
                paste_with_a(background, ranked_challenge_card, (10, pos))
                pos += 340
                total_pos += 340

        # 第四排绘制 默认为X赛
        if contest_match is None or contest_match == "X Schedule":
            if (
                rule_match is None
                or rule_match == xschedule[idx]["xMatchSetting"]["vsRule"]["rule"]
            ):
                count_match_data += 1
                stage = xschedule[idx]["xMatchSetting"]["vsStages"]
                ranked_challenge_card = get_stage_card(
                    ImageInfo(
                        stage[0]["name"],
                        stage[0]["image"]["url"],
                        get_trans_stage(stage[0]["id"]),
                        "对战地图",
                    ),
                    ImageInfo(
                        stage[1]["name"],
                        stage[1]["image"]["url"],
                        get_trans_stage(stage[1]["id"]),
                        "对战地图",
                    ),
                    "X比赛",
                    "X",
                    xschedule[idx]["xMatchSetting"]["vsRule"]["rule"],
                    time_converter(xschedule[idx]["startTime"]),
                    time_converter(xschedule[idx]["endTime"]),
                )
                paste_with_a(background, ranked_challenge_card, (10, pos))
                pos += 340
                total_pos += 340
        # 如果有筛选结果，将时间表头贴到底图上
        if count_match_data:
            # 取涂地模式的时间，除举办祭典外，都可用
            date_time = time_converter_yd(regular[idx]["startTime"])
            start_time = time_converter(regular[idx]["startTime"])
            end_time = time_converter(regular[idx]["endTime"])
            # 绘制时间表头
            time_head_bg = get_time_head_bg(
                time_head_bg_size, date_time, start_time, end_time
            )
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

        # if contest_match is None or contest_match == 'League':
        #     if rule_match is None or rule_match == league[idx]['rule']['name']:
        #         league_card = get_stage_card(
        #             league[idx]['stage_a']['name'],
        #             league[idx]['stage_b']['name'],
        #             'League',
        #             league[idx]['rule']['name'],
        #             time_converter(league[idx]['start_time']),
        #             time_converter(league[idx]['end_time']),
        #         )
        #         paste_with_a(background, league_card, (10, pos))
        #         pos += 340
    # 圆角化
    _, image_background = circle_corner(image_background, radii=16)
    return image_background


# 绘制 打工地图
def get_coop_stages(stage, weapon, time, boss, mode):
    top_size_pos = (0, -2)
    bg_size = (800, len(stage) * 162 + top_size_pos[1])
    stage_bg_size = (300, 160)
    weapon_size = (90, 90)
    boss_size = (40, 40)
    mode_size = (40, 40)

    # 创建纯色背景
    image_background_rgb = dict_bg_rgb["打工"]
    image_background = Image.new("RGBA", bg_size, image_background_rgb)
    bg_mask_size = (300, 200)
    bg_mask = get_file("打工蒙版").resize(bg_mask_size)
    # 填充小图蒙版
    image_background = tiled_fill(image_background, bg_mask)
    # 绘制小鲑鱼
    coop_fish_size = (36, 48)
    coop_fish_img = get_file("小鲑鱼").resize(coop_fish_size)
    coop_fish_img_pos = (6, 8)
    paste_with_a(image_background, coop_fish_img, coop_fish_img_pos)

    # 绘制地图信息
    coop_stage_bg = Image.new("RGBA", (bg_size[0], bg_size[1] + 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(coop_stage_bg)
    font = ImageFont.truetype(ttf_path, 30)
    for pos, val in enumerate(time):
        # 绘制时间文字
        time_text_pos = (40, 5 + pos * 160)
        time_text_size = font.getsize(val)
        dr.text(time_text_pos, val, font=font, fill="#FFFFFF")
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
            weapon_image = get_save_file(val_weapon).resize(
                weapon_size, Image.ANTIALIAS
            )
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
    _, image_background = circle_corner(image_background, radii=20)

    return image_background


# 随机武器
def get_random_weapon(weapon1: [] = None, weapon2: [] = None):
    # 取两组随机武器
    if weapon1 is None:
        weapon1 = random.sample(os.listdir(weapon_folder), k=4)
    if weapon2 is None:
        weapon2 = random.sample(os.listdir(weapon_folder), k=4)
    weapon_size = (122, 158)
    _, image_background = circle_corner(get_file("背景").resize((620, 420)), radii=20)
    dr = ImageDraw.Draw(image_background)
    font = ImageFont.truetype(ttf_path, 50)
    # 绘制中间vs和长横线
    dr.text((278, 160), "VS", font=font, fill="#FFFFFF")
    dr.line([(18, 210), (270, 210)], fill="#FFFFFF", width=4)
    dr.line([(350, 210), (602, 210)], fill="#FFFFFF", width=4)
    # 遍历进行贴图
    for i in range(4):
        image = get_weapon(weapon1[i]).resize(weapon_size, Image.ANTIALIAS)
        image_background.paste(image, ((160 * i + 5), 20))
        image = get_weapon(weapon2[i]).resize(weapon_size, Image.ANTIALIAS)
        image_background.paste(image, ((160 * i + 5), 20 + 220))

    return image_background


# 文本图片  弃用函数
# mode: coop,
# def draw_text_image(text, mode):
#     if mode == 'coop':
#         size = (960, 320)
#     elif mode == 'contest':
#         size = (960, 720)
#     else:
#         size = (1920, 1080)
#     img = Image.new("RGB", size, (255, 255, 255))
#     dr = ImageDraw.Draw(img)
#     font = ImageFont.truetype(ttf_path_chinese, 30)
#     dr.text((10, 5), text, font=font, fill="#000000")
#     return image_to_base64(img)

# if __name__ == '__main__':
#     get_random_weapon().show()
