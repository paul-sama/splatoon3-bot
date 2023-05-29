import io
import os
import random
from io import BytesIO
import urllib3
from PIL import Image, ImageDraw, ImageFont
from .utils import *
from .imageManager import ImageManager

cur_path = os.path.abspath(os.path.join(__file__, os.pardir))

image_folder = os.path.join(cur_path, 'staticData', 'ImageData')
weapon_folder = os.path.join(cur_path, 'staticData', 'weapon')
ttf_path = os.path.join(cur_path, 'staticData', 'SplatoonFontFix.otf')
ttf_path_chinese = os.path.join(cur_path, 'staticData', 'Text.ttf')

imageManager = ImageManager()
http = urllib3.PoolManager()

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return buffered.getvalue()


def get_file(name, format_name='png'):
    img = Image.open(os.path.join(image_folder, '{}.{}'.format(name, format_name)))
    return img

def get_weapon(name):
    return Image.open(os.path.join(weapon_folder, '{}'.format(name)))

def get_file_url(url):
    r = http.request('GET', url, timeout=5)
    return r.data

def get_save_file(img: ImageInfo):
    res = imageManager.get_info(img.name)
    if not res:
        print('[ImageManager] new image {}.'.format(img.name))
        res = get_file_url(img.url)
        imageManager.add_or_modify(img.name, res)
        return Image.open(io.BytesIO(res))
    else:
        return Image.open(io.BytesIO(res[1]))

def get_file_path(name, format_name='png'):
    return os.path.join(image_folder, '{}.{}'.format(name, format_name))

def circle_corner(img, radii):
    """
    圆角处理
    :param img: 源图象。
    :param radii: 半径，如：30。
    :return: 返回一个圆角处理后的图象。
    """
    # 画圆（用于分离4个角）
    circle = Image.new('L', (radii * 2, radii * 2), 0)  # 创建一个黑色背景的画布
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 画白色圆形

    # 原图
    img = img.convert("RGBA")
    w, h = img.size

    # 画4个角（将整圆分离为4个部分）
    alpha = Image.new('L', img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))  # 右上角
    alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii))  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))  # 左下角

    img.putalpha(alpha)  # 白色区域透明可见，黑色区域不可见
    return alpha, img


def paste_with_a(image_background, image_pasted, pos):
    _, _, _, a = image_pasted.convert('RGBA').split()
    image_background.paste(image_pasted, pos, mask=a)


def get_stage_card(stage1, stage2, contest_mode, contest_name, game_mode, start_time, end_time, img_size=(1024, 340)):
    _, image_background = circle_corner(get_file('background').resize(img_size), radii=20)

    stage_size = (int(img_size[0]*0.48), int(img_size[1]*0.7))
    image_left = get_save_file(stage1).resize(stage_size, Image.ANTIALIAS)
    image_right = get_save_file(stage2).resize(stage_size, Image.ANTIALIAS)
    _, image_alpha = circle_corner(image_left, radii=16)

    width_between_stages = int((img_size[0] - 2*stage_size[0])/3)
    start_stage_pos = (width_between_stages, int((img_size[1]-stage_size[1])/8*7))
    image_background.paste(image_left, start_stage_pos, mask=image_alpha)
    next_stage_pos = (start_stage_pos[0] + width_between_stages + stage_size[0], start_stage_pos[1])
    image_background.paste(image_right, next_stage_pos, mask=image_alpha)

    stage_mid_pos = (img_size[0]//2 - 60, img_size[1]//2 - 20)
    image_icon = get_file(contest_name)
    paste_with_a(image_background, image_icon, stage_mid_pos)

    blank_size = (img_size[0], start_stage_pos[1])
    drawer = ImageDraw.Draw(image_background)
    ttf = ImageFont.truetype(ttf_path_chinese, 40)
    drawer.text((40, start_stage_pos[1]-60), contest_mode, font=ttf, fill=(255, 255, 255))
    ttf = ImageFont.truetype(ttf_path_chinese, 40)
    game_mode = trans(game_mode)
    drawer.text((blank_size[0]//3, start_stage_pos[1]-60), game_mode, font=ttf, fill=(255, 255, 255))
    ttf = ImageFont.truetype(ttf_path, 40)
    drawer.text((blank_size[0]*2//3, 20), '{} - {}'.format(start_time, end_time), font=ttf, fill=(255, 255, 255))

    return image_background


def get_stages(schedule, num_list, contest_match=None, rule_match=None):
    regular = schedule['regularSchedules']['nodes']
    ranked = schedule['bankaraSchedules']['nodes']
    # league = schedule['leagueSchedules']['nodes']
    xschedule = schedule['xSchedules']['nodes']
    cnt = 0
    for idx in num_list:
        if contest_match is None or contest_match == 'Turf War':
            cnt += 1

        if contest_match is None or contest_match == 'Ranked Challenge':
            if rule_match is None or rule_match == ranked[idx]['bankaraMatchSettings'][0]['vsRule']['rule']:
                cnt += 1

        if contest_match is None or contest_match == 'Ranked Open':
            if rule_match is None or rule_match == ranked[idx]['bankaraMatchSettings'][1]['vsRule']['rule']:
                cnt += 1

        if contest_match is None or contest_match == 'X Schedule':
            if rule_match is None or rule_match == xschedule[idx]['xMatchSetting']['vsRule']['rule']:
                cnt += 1
    if cnt == 0:
        return None
    background = Image.new('RGB', (1044, 340*cnt), (41, 36, 33))
    pos = 0
    for idx in num_list:
        if contest_match is None or contest_match == 'Turf War':
            regular_card = get_stage_card(
                ImageInfo(regular[idx]['regularMatchSetting']['vsStages'][0]['name'], regular[idx]['regularMatchSetting']['vsStages'][0]['image']['url']),
                ImageInfo(regular[idx]['regularMatchSetting']['vsStages'][1]['name'], regular[idx]['regularMatchSetting']['vsStages'][1]['image']['url']),
                '涂地模式', 'Regular',
                regular[idx]['regularMatchSetting']['vsRule']['rule'],
                time_converter(regular[idx]['startTime']),
                time_converter(regular[idx]['endTime']),
            )
            paste_with_a(background, regular_card, (10, pos))
            pos += 340

        if contest_match is None or contest_match == 'Ranked Challenge':
            if rule_match is None or rule_match == ranked[idx]['bankaraMatchSettings'][0]['vsRule']['rule']:
                ranked_challenge_card = get_stage_card(
                    ImageInfo(ranked[idx]['bankaraMatchSettings'][0]['vsStages'][0]['name'], ranked[idx]['bankaraMatchSettings'][0]['vsStages'][0]['image']['url']),
                    ImageInfo(ranked[idx]['bankaraMatchSettings'][0]['vsStages'][1]['name'], ranked[idx]['bankaraMatchSettings'][0]['vsStages'][1]['image']['url']),
                    '真格模式-挑战', 'Ranked-Challenge',
                    ranked[idx]['bankaraMatchSettings'][0]['vsRule']['rule'],
                    time_converter(ranked[idx]['startTime']),
                    time_converter(ranked[idx]['endTime']),
                )
                paste_with_a(background, ranked_challenge_card, (10, pos))
                pos += 340

        if contest_match is None or contest_match == 'Ranked Open':
            if rule_match is None or rule_match == ranked[idx]['bankaraMatchSettings'][1]['vsRule']['rule']:
                ranked_challenge_card = get_stage_card(
                    ImageInfo(ranked[idx]['bankaraMatchSettings'][1]['vsStages'][0]['name'], ranked[idx]['bankaraMatchSettings'][1]['vsStages'][0]['image']['url']),
                    ImageInfo(ranked[idx]['bankaraMatchSettings'][1]['vsStages'][1]['name'], ranked[idx]['bankaraMatchSettings'][1]['vsStages'][1]['image']['url']),
                    '真格模式-开放', 'Ranked-Open',
                    ranked[idx]['bankaraMatchSettings'][1]['vsRule']['rule'],
                    time_converter(ranked[idx]['startTime']),
                    time_converter(ranked[idx]['endTime']),
                )
                paste_with_a(background, ranked_challenge_card, (10, pos))
                pos += 340

        if contest_match is None or contest_match == 'X Schedule':
            if rule_match is None or rule_match == xschedule[idx]['xMatchSetting']['vsRule']['rule']:
                ranked_challenge_card = get_stage_card(
                    ImageInfo(xschedule[idx]['xMatchSetting']['vsStages'][0]['name'],
                              xschedule[idx]['xMatchSetting']['vsStages'][0]['image']['url']),
                    ImageInfo(xschedule[idx]['xMatchSetting']['vsStages'][1]['name'],
                              xschedule[idx]['xMatchSetting']['vsStages'][1]['image']['url']),
                    'X段模式', 'X',
                    xschedule[idx]['xMatchSetting']['vsRule']['rule'],
                    time_converter(xschedule[idx]['startTime']),
                    time_converter(xschedule[idx]['endTime']),
                )
                paste_with_a(background, ranked_challenge_card, (10, pos))
                pos += 340

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
    return image_to_base64(background)


def get_coop_stages(stage_first, weapon_first, info_first, stage_second, weapon_second, info_second):
    img_size = (300, 160)
    weapon_size = (90, 90)
    _, image_background = circle_corner(get_file('background').resize((800, 320)), radii=20)
    dr = ImageDraw.Draw(image_background)
    font = ImageFont.truetype(ttf_path, 30)
    dr.text((60, 5), info_first, font=font, fill="#FFFFFF")
    dr.text((60, 160), info_second, font=font, fill="#FFFFFF")
    image1 = get_save_file(stage_first).resize(img_size, Image.ANTIALIAS)
    image2 = get_save_file(stage_second).resize(img_size, Image.ANTIALIAS)
    image_background.paste(image1, (500, 0))
    image_background.paste(image2, (500, 160))
    for i in range(4):
        image = get_save_file(weapon_first[i]).resize(weapon_size, Image.ANTIALIAS)
        image_background.paste(image, (120 * i + 20, 60))
        image = get_save_file(weapon_second[i]).resize(weapon_size, Image.ANTIALIAS)
        image_background.paste(image, (120 * i + 20, 60 + 160))

    return image_to_base64(image_background)


def get_all_coop_stages(stage, weapon, info):
    img_size = (300, 160)
    weapon_size = (90, 90)
    _, image_background = circle_corner(get_file('background').resize((800, len(stage)*160)), radii=20)
    dr = ImageDraw.Draw(image_background)
    font = ImageFont.truetype(ttf_path, 30)
    for (pos, val) in enumerate(info):
        dr.text((60, 5 + pos*160), val, font=font, fill="#FFFFFF")
    for (pos, val) in enumerate(stage):
        img = get_save_file(val).resize(img_size, Image.ANTIALIAS)
        image_background.paste(img, (500, 160*pos))
        for (pos_weapon, val_weapon) in enumerate(weapon[pos]):
            image = get_save_file(val_weapon).resize(weapon_size, Image.ANTIALIAS)
            image_background.paste(image, (120 * pos_weapon + 20, 60 + 160*pos))

    return image_to_base64(image_background)


def get_random_weapon(weapon1: [] = None, weapon2: [] = None):
    if weapon1 is None:
        weapon1 = random.sample(os.listdir(weapon_folder), k=4)
    if weapon2 is None:
        weapon2 = random.sample(os.listdir(weapon_folder), k=4)
    weapon_size = (122, 158)
    _, image_background = circle_corner(get_file('background').resize((620, 420)), radii=20)
    dr = ImageDraw.Draw(image_background)
    font = ImageFont.truetype(ttf_path, 50)
    dr.text((278, 160), 'VS', font=font, fill="#FFFFFF")
    dr.line([(18, 210), (270, 210)], fill="#FFFFFF", width=4)
    dr.line([(350, 210), (602, 210)], fill="#FFFFFF", width=4)
    for i in range(4):
        image = get_weapon(weapon1[i]).resize(weapon_size, Image.ANTIALIAS)
        image_background.paste(image, ((160 * i + 5), 20))
        image = get_weapon(weapon2[i]).resize(weapon_size, Image.ANTIALIAS)
        image_background.paste(image, ((160 * i + 5), 20 + 220))

    return image_to_base64(image_background)

# mode: coop,
def draw_text_image(text, mode):
    if mode == 'coop':
        size = (960, 320)
    elif mode == 'contest':
        size = (960, 720)
    else:
        size = (1920, 1080)
    im = Image.new("RGB", size, (255, 255, 255))
    dr = ImageDraw.Draw(im)
    font = ImageFont.truetype(ttf_path_chinese, 30)
    dr.text((10, 5), text, font=font, fill="#000000")
    return image_to_base64(im)


# if __name__ == '__main__':
#     get_random_weapon().show()