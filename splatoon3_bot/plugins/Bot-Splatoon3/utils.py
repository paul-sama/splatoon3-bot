import datetime

# dict
dict_contest = {
    "涂地": "Turf War",
    "挑战": "Ranked Challenge",
    "开放": "Ranked Open",
    "X段": "X Schedule",
}
dict_rule = {
    "区域": "AREA",
    "蛤蜊": "CLAM",
    "塔楼": "LOFT",
    "鱼虎": "GOAL",
}

# 触发关键词  同义文本替换
dict_keyword_replace = {
    "\\": "",
    "/": "",
    ".": "",
    "。": "",
    "涂涂": "涂地",
    "组排": "开放",
    "排排": "开放",
    "pp": "开放",
    "PP": "开放",
    "真格": "挑战",
    "x段": "X段",
    "X赛": "X段",
    "x赛": "X段",
    "推塔": "塔楼",
    "抢塔": "塔楼",
    "抢鱼": "鱼虎",
    "鲑鱼跑": "工",
    "团队打工": "工",
    "打工": "工",
    "big run": "工",
    "bigrun": "工",
    "help": "帮助",
    "衣服": "装备",
}

# 背景 rgb颜色
dict_bg_rgb = {
    "Turf War": (24, 200, 26),
    "Ranked Challenge": (227, 68, 17),
    "Ranked Open": (24, 200, 26),
    "X Schedule": (14, 205, 147),
    "打工": (14, 203, 146),
    "活动": (223, 42, 119),
}


# 群白名单
white_list = ["458482582", "792711635", "835723997", "578031026", "1607044636"]


# 类 图片信息 自身转化为对象
class ImageInfo:
    def __init__(self, name, url, zh_name, source_type):
        self.name = name
        self.url = url
        self.zh_name = zh_name
        self.source_type = source_type


# 类 数据库 Weapon_Data
class WeaponData:
    # zh 字段暂且预留，方便后续翻译的进行
    # 为了便于先进行 INFO 信息的查询，image 字段默认留空
    def __init__(
        self,
        name,
        sub_name,
        special_name,
        special_points,
        level,
        weapon_class,
        image=None,
        sub_image=None,
        special_image=None,
        weapon_class_image=None,
        zh_name="None",
        zh_sub_name="None",
        zh_special_name="None",
    ):
        self.name = name
        self.image = image
        self.sub_name = sub_name
        self.sub_image = sub_image
        self.special_name = special_name
        self.special_image = special_image
        self.special_points = special_points
        self.level = level
        self.weapon_class = weapon_class
        self.weapon_class_image = weapon_class_image
        self.zh_name = zh_name
        self.zh_sub_name = zh_sub_name
        self.zh_special_name = zh_special_name


# 批量替换文本
def multiple_replace(text):
    for key in dict_keyword_replace:
        text = text.replace(key, dict_keyword_replace[key])
    return text


# 时间转换 月-日
def time_converter_yd(time_str):
    # convert time to UTC+8
    dt = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    dt += datetime.timedelta(hours=8)
    return datetime.datetime.strftime(dt, "%m.%d")


# 时间转换 时:分
def time_converter(time_str):
    # convert time to UTC+8
    dt = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    dt += datetime.timedelta(hours=8)
    return datetime.datetime.strftime(dt, "%H:%M")


# 时间转换 月-日 时:分
def time_converter_day(time_str):
    # convert time to UTC+8
    dt = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    dt += datetime.timedelta(hours=8)
    return datetime.datetime.strftime(dt, "%m-%d %H:%M")


# 获取年月日
def get_time_ymd():
    # convert time to UTC+8
    dt = datetime.datetime.now().strftime("%Y-%m-%d")
    return dt


# 校验群号
def check_group_id(group_id):
    # if group_id == '616533832':
    #     return False
    return True
