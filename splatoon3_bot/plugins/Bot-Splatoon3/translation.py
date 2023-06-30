import json
import httpx

from nonebot.log import logger

from .utils import get_time_ymd

# 翻译字典 rule
dict_rule_trans = {
    "LOFT": "真格塔楼",
    "CLAM": "真格蛤蜊",
    "GOAL": "真格鱼虎",
    "AREA": "真格区域",
    "TURF_WAR": "占地对战",
}

# 翻译字典 装备 副武器
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


# 翻译字典 装备 大招
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

# 鲑鱼跑模式
list_salmonrun_mode = ["一般打工", "团队打工", "大型跑"]

trans_res = None
trans_res_save_ymd: str


# 取翻译数据
def get_trans_data():
    global trans_res
    global trans_res_save_ymd
    if trans_res is None or check_expire_trans(trans_res_save_ymd):
        logger.info("重新请求:翻译文本")
        with httpx.Client() as client:
            result = client.get("https://splatoon3.ink/data/locale/zh-CN.json")
            trans_res = json.load(result)
            # 刷新储存时 时间
            trans_res_save_ymd = get_time_ymd()
            return trans_res
    else:
        return trans_res


# 校验过期翻译 记录每日ymd，不同则为false，使其每日刷新一次
def check_expire_trans(trans_res_save_ymd):
    now_ymd = get_time_ymd()
    if now_ymd != trans_res_save_ymd:
        return True
    return False


# 获取地图翻译名
def get_trans_stage(id: str):
    global trans_res
    zh_name = trans_res["stages"][id]["name"]
    if zh_name == "":
        return "未取得翻译名称"
    return zh_name


# 获取武器翻译名
def get_trans_weapon(id: str):
    global trans_res
    zh_name = trans_res["weapons"][id]["name"]
    if zh_name == "":
        return "未取得翻译名称"
    return zh_name


# 用现有翻译字典对游戏模式进行翻译
def get_trans_game_mode(text):
    if text in dict_rule_trans:
        return dict_rule_trans[text]
    return text
