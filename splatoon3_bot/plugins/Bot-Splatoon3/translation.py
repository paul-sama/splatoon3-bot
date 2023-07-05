import json
import random
import httpx

from nonebot.log import logger
from .utils import get_time_ymd, cf_http_get

trans_res = None
trans_res_save_ymd: str
# 武器图片类型
weapon_image_type = ["Main", "Sub", "Special", "Class", "Father_Class"]


# 取翻译数据
def get_trans_data():
    global trans_res
    global trans_res_save_ymd
    if trans_res is None or check_expire_trans(trans_res_save_ymd):
        logger.info("重新请求:翻译文本")
        result = cf_http_get("https://splatoon3.ink/data/locale/zh-CN.json").text
        trans_res = json.loads(result)
        # 刷新储存时 时间
        trans_res_save_ymd = get_time_ymd()
        return trans_res
    else:
        return trans_res


# 校验过期翻译 记录每日ymd，不同则为false，使其每日刷新一次
def check_expire_trans(_trans_res_save_ymd):
    now_ymd = get_time_ymd()
    if now_ymd != _trans_res_save_ymd:
        return True
    return False


# 获取地图翻译名
def get_trans_stage(_id: str):
    global trans_res
    zh_name = trans_res["stages"][_id]["name"]
    if zh_name == "":
        return "未取得翻译名称"
    return zh_name


# 获取武器翻译名
def get_trans_weapon(_id: str):
    global trans_res
    zh_name = trans_res["weapons"][_id]["name"]
    if zh_name == "":
        return "未取得翻译名称"
    return zh_name


# 用现有翻译字典对游戏模式进行翻译
def get_trans_game_mode(text):
    if text in dict_rule_reverse_trans:
        return dict_rule_reverse_trans[text]
    return text


# 装备 语义词转换,并返回语义词类别
def weapon_semantic_word_conversion(word: str):
    word_type = weapon_image_type
    # 判断这个语义词是属于 类别，副武器，大招
    if word in dict_weapon_class:
        return word_type[3], dict_weapon_class.get(word)
    if word in dict_weapon_sub:
        return word_type[1], dict_weapon_sub.get(word)
    if word in dict_weapon_special:
        return word_type[2], dict_weapon_special.get(word)
    # 没有任何匹配时，取随机大类别
    # 遍历values
    father_class_list = []
    for v in dict_weapon_class.values():
        father_class_list.append(dict_weapon_father_class_trans.get(v))
    return word_type[4], random.choice(list(father_class_list))


# 翻译字典
dict_rule_reverse_trans = {
    "LOFT": "真格塔楼",
    "CLAM": "真格蛤蜊",
    "GOAL": "真格鱼虎",
    "AREA": "真格区域",
    "TURF_WAR": "占地对战",
}
# dict
dict_contest_trans = {
    "涂地": "Turf War",
    "挑战": "Ranked Challenge",
    "开放": "Ranked Open",
    "X段": "X Schedule",
}
dict_rule_trans = {
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

# 规范翻译字典 装备 主武器名称
dict_weapon_main_trans = {}

# 规范翻译字典 装备 副武器名称
dict_weapon_sub_trans = {
    "Splat Bomb": "斯普拉炸弹",
    "Suction Bomb": "吸盘炸弹",
    "Burst Bomb": "快速炸弹",
    "Sprinkler": "洒墨器",
    "Splash Wall": "斯普拉防护墙",
    "Fizzy Bomb": "碳酸炸弹",
    "Curling Bomb": "冰壶炸弹",
    "Autobomb": "机器人炸弹",
    "Squid Beakon": "跳跃信标",
    "Point Sensor": "定点侦测器",
    "Ink Mine": "墨汁陷阱",
    "Toxic Mist": "毒雾",
    "Angle Shooter": "标线器",
    "Torpedo": "鱼雷",
}

# 规范翻译字典 装备 大招名称
dict_weapon_special_trans = {
    "Trizooka": "终极发射",
    "Big Bubbler": "巨大防护罩",
    "Zipcaster": "触手喷射",
    "Tenta Missiles": "多重导弹",
    "Ink Storm": "墨雨云",
    "Booyah Bomb": "赞气弹",
    "Wave Breaker": "弹跳声呐",
    "Ink Vac": "吸墨机",
    "Killer Wail 5.1": "喇叭辐射5.1ch",
    "Inkjet": "喷射背包",
    "Ultra Stamp": "终极印章",
    "Crab Tank": "螃蟹坦克",
    "Reefslider": "鲨鱼坐骑",
    "Triple Inkstrike": "三重龙卷风",
    "Tacticooler": "能量站",
    "Super Chump": "诱饵烟花",
    "Kraken Royale": "帝王鱿鱼",
}

# 规范翻译字典 装备 类别名称
dict_weapon_class_trans = {
    "Shooter": "射击枪",
    "Blaster": "爆破枪",
    "Brella": "伞",
    "Brush": "笔刷",
    "Charger": "狙击枪",
    "Dualie": "双枪",
    "Roller": "滚筒",
    "Slosher": "泼桶",
    "Splatana": "刮水刀",
    "Splatling": "旋转枪",
    "Stringer": "弓",
}

# 武器类别 归属大类
dict_weapon_father_class_trans = {
    "射击枪": "近距离",
    "爆破枪": "中距离",
    "伞": "近距离",
    "笔刷": "近距离",
    "狙击枪": "长距离",
    "双枪": "近距离",
    "滚筒": "近距离",
    "泼桶": "中距离",
    "刮水刀": "中距离",
    "旋转枪": "长距离",
    "弓": "长距离",
}

# 语义化字典 装备 副武器
dict_weapon_sub = {
    "斯普拉炸弹": "斯普拉炸弹",
    "三角雷": "斯普拉炸弹",
    "吸盘炸弹": "吸盘炸弹",
    "粘弹": "吸盘炸弹",
    "黏弹": "吸盘炸弹",
    "快速炸弹": "快速炸弹",
    "水球": "快速炸弹",
    "洒墨器": "洒墨器",
    "花洒": "洒墨器",
    "斯普拉防护墙": "斯普拉防护墙",
    "水帘": "斯普拉防护墙",
    "帘子": "斯普拉防护墙",
    "雨帘": "斯普拉防护墙",
    "碳酸炸弹": "碳酸炸弹",
    "碳酸": "碳酸炸弹",
    "摇摇乐": "碳酸炸弹",
    "冰壶炸弹": "冰壶炸弹",
    "冰壶": "冰壶炸弹",
    "机器人炸弹": "机器人炸弹",
    "小鸡雷": "机器人炸弹",
    "小鸡": "机器人炸弹",
    "跳跃信标": "跳跃信标",
    "跳点": "跳跃信标",
    "信标": "跳跃信标",
    "定点侦测器": "定点侦测器",
    "狗链": "定点侦测器",
    "狗环": "定点侦测器",
    "墨汁陷阱": "墨汁陷阱",
    "陷阱": "墨汁陷阱",
    "地雷": "墨汁陷阱",
    "毒雾": "毒雾",
    "毒瓶": "毒雾",
    "标线器": "标线器",
    "马克笔": "标线器",
    "鱼雷": "鱼雷",
}

# 语义化字典 装备 大招
dict_weapon_special = {
    "终极发射": "终极发射",
    "rpg": "终极发射",
    "RPG": "终极发射",
    "巨大防护罩": "巨大防护罩",
    "防护罩": "巨大防护罩",
    "触手喷射": "触手喷射",
    "触手": "触手喷射",
    "蜘蛛侠": "触手喷射",
    "多重导弹": "多重导弹",
    "导弹": "多重导弹",
    "墨雨云": "墨雨云",
    "下雨": "墨雨云",
    "赞气弹": "赞气弹",
    "nice弹": "赞气弹",
    "弹跳声呐": "弹跳声呐",
    "跳蛋": "弹跳声呐",
    "声呐": "弹跳声呐",
    "吸墨机": "吸墨机",
    "吸尘器": "吸墨机",
    "喇叭辐射5.1ch": "喇叭辐射5.1ch",
    "镭射": "喇叭辐射5.1ch",
    "激光": "喇叭辐射5.1ch",
    "喷射背包": "喷射背包",
    "喷气背包": "喷射背包",
    "飞机": "喷射背包",
    "jet": "喷射背包",
    "JET": "喷射背包",
    "终极印章": "终极印章",
    "印章": "终极印章",
    "锤子": "终极印章",
    "大锤": "终极印章",
    "螃蟹坦克": "螃蟹坦克",
    "螃蟹": "螃蟹坦克",
    "鲨鱼坐骑": "鲨鱼坐骑",
    "鲨鱼": "鲨鱼坐骑",
    "三重龙卷风": "三重龙卷风",
    "龙卷风": "三重龙卷风",
    "能量站": "能量站",
    "饮料站": "能量站",
    "饮料": "能量站",
    "诱饵烟花": "诱饵烟花",
    "反击狼烟": "诱饵烟花",
    "烟花": "诱饵烟花",
    "诱饵": "诱饵烟花",
    "帝王鱿鱼": "帝王鱿鱼",
    "鱿鱼": "帝王鱿鱼",
    "帝王乌贼": "帝王鱿鱼",
    "大王乌贼": "帝王鱿鱼",
}

# 语义化字典 装备类别
dict_weapon_class = {
    "射击枪": "射击枪",
    "小枪": "射击枪",
    "爆破枪": "爆破枪",
    "泡": "爆破枪",
    "炮": "爆破枪",
    "伞": "伞",
    "笔刷": "笔刷",
    "画笔": "笔刷",
    "刷子": "笔刷",
    "笔": "笔刷",
    "狙击枪": "狙击枪",
    "狙": "狙击枪",
    "双枪": "双枪",
    "滚筒": "滚筒",
    "筒": "滚筒",
    "刷": "滚筒",
    "泼桶": "泼桶",
    "桶": "泼桶",
    "刮水刀": "刮水刀",
    "电锯": "刮水刀",
    "锯": "刮水刀",
    "水刀": "刮水刀",
    "刀": "刮水刀",
    "旋转枪": "旋转枪",
    "加特林": "旋转枪",
    "加": "旋转枪",
    "弓": "弓",
}

# 鲑鱼跑模式
list_salmonrun_mode = ["一般打工", "团队打工", "大型跑"]
