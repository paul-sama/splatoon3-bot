from ..data import (
    get_coop_info,
    get_stage_info,
    get_weapon_info,
    get_schedule_data,
)
from .image_processer import *
from .image_processer_tools import image_to_base64

time_format_ymdh = "%Y-%m-%dT%H"


# 取 打工图片
def get_coop_stages_image(*args):
    _all = args[0]
    # 获取数据
    stage, weapon, time, boss, mode = get_coop_info(_all)
    # 绘制图片
    image = get_coop_stages(stage, weapon, time, boss, mode)
    return image


# 取 对战图片
def get_stages_image(*args):
    num_list = args[0]
    contest_match = args[1]
    rule_match = args[2]
    logger.info("num_list为:" + str(num_list))
    logger.info("contest_match为:" + str(contest_match))
    logger.info("rule_match为:" + str(rule_match))
    # 获取数据
    schedule, new_num_list, new_contest_match, new_rule_match = get_stage_info(num_list, contest_match, rule_match)
    # 绘制图片
    image = get_stages(schedule, new_num_list, new_contest_match, new_rule_match)
    return image


# 取 祭典图片
def get_festival_image(*args):
    festivals = get_festivals_data()["JP"]["data"]["festRecords"]["nodes"]
    image = get_festival(festivals)
    return image


# 取 活动图片
def get_events_image(*args):
    schedule = get_schedule_data()
    events = schedule["eventSchedules"]["nodes"]
    # 如果存在活动
    if len(events) > 0:
        image = get_events(events)
        return image
    else:
        return None


# 取 帮助图片
def get_help_image(*args):
    image = get_help()
    return image


# 取 新版 随机武器图片 不能进行缓存，这个需要实时生成
def get_random_weapon_image(*args):
    plain_text = args[0]
    # 判断是否有空格
    list_weapon = []
    # 是否携带参数
    if "完全随机" in plain_text:
        for v in range(4):
            list_weapon.append({"type": "zh_father_class", "name": ""})
    elif " " in plain_text:
        args = plain_text.split(" ")
        args = args[1:]
        # 如果参数超出
        if len(args) > 4:
            args = args[:4]
        for v in args:
            _type, name = weapon_semantic_word_conversion(v)
            list_weapon.append({"type": _type, "name": name})
        # 如果数量不够四个,用随机大类组别来填充
        if len(list_weapon) < 4:
            for v in range(4 - len(list_weapon)):
                _type, name = weapon_semantic_word_conversion("")
                list_weapon.append({"type": _type, "name": name})
    else:
        # 四个全部用随机大类组别填充
        for v in range(4):
            _type, name = weapon_semantic_word_conversion("")
            list_weapon.append({"type": _type, "name": name})
    # 日志输出组别list信息
    logger.info("武器筛选条件为:" + json.dumps(list_weapon, ensure_ascii=False))
    # 按照 list_weapon 要求随机从sql数据库查找数据
    weapon1, weapon2 = get_weapon_info(list_weapon)
    # 进行乱序
    random.shuffle(weapon1)
    random.shuffle(weapon2)

    # 绘制图片
    image = get_random_weapon(weapon1, weapon2)
    return image


# 测试武器数据库能否取到数据
def get_weapon_info_test():
    res = imageDB.get_weapon_info("", "", "", "")
    if res is not None:
        return True
    else:
        return False


# 计算过期时间 字符串 精确度为 ymdh
def get_expire_time():
    # 计算过期时间
    time_now = datetime.datetime.now()
    time_now_h = time_now.hour
    # 计算过期时间字符串
    # 判断当前小时是奇数还是偶数
    expire_time: datetime
    if (time_now_h % 2) == 0:
        # 偶数
        expire_time = time_now + datetime.timedelta(hours=2)
    else:
        expire_time = time_now + datetime.timedelta(hours=1)
    expire_time_str = expire_time.strftime(time_format_ymdh).strip()
    return expire_time_str


# 向数据库新增或读取图片二进制  缓存图片
def get_save_temp_image(trigger_word, func, *args):
    res = imageDB.get_img_temp(trigger_word)
    image: bytes
    if not res:
        # 重新生成图片并写入
        image_data = func(*args)
        if image_data is None:
            return image_data
        image = image_to_base64(image_data)
        if len(image) != 0:
            logger.info("[ImageDB] new temp image {}".format(trigger_word))
            imageDB.add_or_modify_IMAGE_TEMP(trigger_word, image, get_expire_time())
        return image
    else:
        image_expire_time = res.get("image_expire_time")
        image_data = res.get("image_data")
        # 判断时间是否过期
        expire_time = datetime.datetime.strptime(image_expire_time, time_format_ymdh)
        time_now = datetime.datetime.now()
        if time_now >= expire_time:
            # 重新生成图片并写入
            image_data = func(*args)
            image = image_to_base64(image_data)
            if len(image) != 0:
                logger.info("[ImageDB] update temp image {}".format(trigger_word))
                imageDB.add_or_modify_IMAGE_TEMP(trigger_word, image, get_expire_time())
            return image
        else:
            logger.info("数据库内存在时效范围内的缓存图片，将从数据库读取缓存图片")
            return image_to_base64(Image.open(io.BytesIO(image_data)))


# 写出武器翻译字典
def write_weapon_trans_dict():
    weapon_trans_dict = imageDB.get_all_weapon_info()
    if len(weapon_trans_dict) > 0:
        with open("weapon_trans_dict.txt", "a") as file:
            file.write("{")
        for val in weapon_trans_dict:
            # s += '"' + val["name"] + '":"' + val["zh_name"] + '",'
            s = '"{}":"{}",'.format(val["name"], val["zh_name"])
            with open("weapon_trans_dict.txt", "a") as file:
                file.write(s)
        with open("weapon_trans_dict.txt", "a") as file:
            file.write("}")


# 旧版 取 随机武器图片 不能进行缓存，这个需要实时生成
# def old_get_random_weapon_image(*args):
#     weapon1 = args[0]
#     weapon2 = args[1]
#     # 绘制图片
#     image = old_get_random_weapon(weapon1, weapon2)
#     return image_to_base64(image)
