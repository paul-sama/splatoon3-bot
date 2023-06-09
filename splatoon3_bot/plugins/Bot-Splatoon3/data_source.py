import json

import httpx
import urllib3

from nonebot.log import logger
from playwright.async_api import Browser, async_playwright

from ._class import ImageInfo
from .image_processer import imageDB
from .translation import (
    get_trans_stage,
    get_trans_weapon,
    get_trans_data,
    list_salmonrun_mode,
    dict_contest_trans,
    dict_rule_trans,
    weapon_image_type,
)
from .utils import *

schedule_res = None
http = urllib3.PoolManager()
_browser = None


# 初始化 browser 并唤起
async def init_browser() -> Browser:
    global _browser
    p = await async_playwright().start()
    _browser = await p.chromium.launch()
    return _browser


# 获取目前唤起的 browser
async def get_browser() -> Browser:
    global _browser
    if _browser is None or not _browser.is_connected():
        _browser = await init_browser()
    return _browser


# 通过 browser 获取 shot_url 中的网页截图
async def get_screenshot(shot_url, shot_path=None):
    # playwright 要求不能有多个 browser 被同时唤起
    browser = await get_browser()
    context = await browser.new_context(viewport={"width": 1480, "height": 900}, locale="zh-CH")
    page = await context.new_page()
    await page.set_viewport_size({"width": 1480, "height": 900})
    await page.goto(shot_url)
    try:
        await page.wait_for_timeout(3000)
        if shot_path is None:
            return await page.screenshot()
        else:
            await page.screenshot(path=shot_path)
    except Exception as e:
        logger.error("Screenshot failed" + str(e))
        return await page.screenshot(full_page=True)
    finally:
        await context.close()


# 取日程数据
def get_schedule_data():
    # 校验过期日程
    def check_expire_schedule(schedule):
        st = datetime.datetime.strptime(schedule["regularSchedules"]["nodes"][0]["startTime"], "%Y-%m-%dT%H:%M:%SZ")
        ed = datetime.datetime.strptime(schedule["regularSchedules"]["nodes"][0]["endTime"], "%Y-%m-%dT%H:%M:%SZ")
        nw = datetime.datetime.now() - datetime.timedelta(hours=8)
        if st < nw < ed:
            return False
        return True

    global schedule_res
    if schedule_res is None or check_expire_schedule(schedule_res):
        logger.info("重新请求:日程数据")
        result = cf_http_get("https://splatoon3.ink/data/schedules.json").text
        schedule_res = json.loads(result)
        schedule_res = schedule_res["data"]
        return schedule_res
    else:
        return schedule_res


# 取 打工 信息
def get_coop_info(_all=None):
    # 取地图信息
    def get_stage_image_info(sch):  # sch为schedule[idx]
        return ImageInfo(
            sch["setting"]["coopStage"]["name"],
            sch["setting"]["coopStage"]["image"]["url"],
            get_trans_stage(sch["setting"]["coopStage"]["id"]),
            "打工地图",
        )

    # 取装备信息
    def get_weapon_image_info(sch):  # sch为schedule[idx]
        # for i in range(4) 是循环执行4次，不是多余的代码
        return [
            ImageInfo(
                sch["setting"]["weapons"][i]["name"],
                sch["setting"]["weapons"][i]["image"]["url"],
                get_trans_weapon(sch["setting"]["weapons"][i]["__splatoon3ink_id"]),
                "武器",
            )
            for i in range(4)
        ]

    # 取时间信息
    def get_str_time(sch):
        _start_time = time_converter_day(sch["startTime"])
        _end_time = time_converter_day(sch["endTime"])
        return "{} - {}".format(_start_time, _end_time)

    # 取boss名称
    def get_str_boss(sch):
        return sch["__splatoon3ink_king_salmonid_guess"]

    # 校验普通打工时间，是否在特殊打工模式之后
    def check_salmonrun_time(_start_time, _special_mode_start_time):
        # 输入时间都缺少年份，需要手动补充一个年份后还原为date对象
        year = datetime.datetime.now().year
        _start_time = str(year) + "-" + _start_time
        _special_mode_start_time = str(year) + "-" + _special_mode_start_time
        st = datetime.datetime.strptime(_start_time, "%Y-%m-%d %H:%M")
        su_st = datetime.datetime.strptime(_special_mode_start_time, "%Y-%m-%d %H:%M")
        if st > su_st:
            return True
        return False

    # 取日程
    schedule = get_schedule_data()
    # 取翻译
    get_trans_data()
    # 一般打工数据
    regular_schedule = schedule["coopGroupingSchedule"]["regularSchedules"]["nodes"]
    # 团队打工竞赛
    team_schedule = schedule["coopGroupingSchedule"]["teamContestSchedules"]["nodes"]
    # big run 数据
    bigrun_schedule = schedule["coopGroupingSchedule"]["bigRunSchedules"]["nodes"]
    stage = []
    weapon = []
    time = []
    boss = []
    mode = []
    schedule = regular_schedule
    if not _all:
        # 只输出两排
        for i in range(2):
            stage.append(get_stage_image_info(schedule[i]))
            weapon.append(get_weapon_image_info(schedule[i]))
            time.append(get_str_time(schedule[i]))
            boss.append(get_str_boss(schedule[i]))
            mode.append(list_salmonrun_mode[0])
    else:
        # 输出全部(五排)
        stage = [get_stage_image_info(sch) for sch in schedule]
        weapon = [get_weapon_image_info(sch) for sch in schedule]
        time = [get_str_time(sch) for sch in schedule]
        boss = [get_str_boss(sch) for sch in schedule]
        mode = [list_salmonrun_mode[0] for sch in schedule]

    # 如果存在 团队打工
    if len(team_schedule) != 0:
        schedule = team_schedule
        # 计算插入索引
        insert_idx = 0
        need_offset = False
        special_mode_start_time = get_str_time(schedule[0]).split(" - ")[0]
        for k, v in enumerate(time):
            start_time = v.split(" - ")[0]
            if check_salmonrun_time(start_time, special_mode_start_time):
                insert_idx = k
                need_offset = True
                break
        if not need_offset:
            insert_idx = len(time)
        # 插入数据
        stage.insert(insert_idx, get_stage_image_info(schedule[0]))
        weapon.insert(insert_idx, get_weapon_image_info(schedule[0]))
        time.insert(insert_idx, get_str_time(schedule[0]))
        # 团队打工取不到boss信息
        boss.insert(insert_idx, "")
        mode.insert(insert_idx, list_salmonrun_mode[1])

    # 如果存在 bigrun
    if len(bigrun_schedule) != 0:
        schedule = bigrun_schedule
        # 计算插入索引
        insert_idx = 0
        need_offset = False
        special_mode_start_time = get_str_time(schedule[0]).split(" - ")[0]
        for k, v in enumerate(time):
            start_time = v.split(" - ")[0]
            if check_salmonrun_time(start_time, special_mode_start_time):
                insert_idx = k
                need_offset = True
                break
        if not need_offset:
            insert_idx = len(time)
        # 插入数据
        stage.insert(insert_idx, get_stage_image_info(schedule[0]))
        weapon.insert(insert_idx, get_weapon_image_info(schedule[0]))
        time.insert(insert_idx, get_str_time(schedule[0]))
        # 团队打工取不到boss信息
        boss.insert(insert_idx, "")
        mode.insert(insert_idx, list_salmonrun_mode[2])

    return stage, weapon, time, boss, mode


# 取 装备信息
def get_weapon_info(list_weapon: list):
    weapon1 = []
    weapon2 = []
    for v in list_weapon:
        _type = v["type"]
        name = v["name"]
        zh_weapon_class = ""
        zh_weapon_sub = ""
        zh_weapon_special = ""
        zh_father_class = ""
        if _type == weapon_image_type[3]:
            # class
            zh_weapon_class = name
        elif _type == weapon_image_type[1]:
            # sub
            zh_weapon_sub = name
        elif _type == weapon_image_type[2]:
            # special
            zh_weapon_special = name
        elif _type == weapon_image_type[4]:
            # father_class
            zh_father_class = name
        weaponData = imageDB.get_weapon_info(zh_weapon_class, zh_weapon_sub, zh_weapon_special, zh_father_class)
        weaponData2 = imageDB.get_weapon_info(zh_weapon_class, zh_weapon_sub, zh_weapon_special, zh_father_class)
        # 获取图片数据
        # Main
        weaponData.image = imageDB.get_weapon_image(weaponData.name, weapon_image_type[0]).get("image")
        weaponData2.image = imageDB.get_weapon_image(weaponData2.name, weapon_image_type[0]).get("image")
        # Sub
        weaponData.sub_image = imageDB.get_weapon_image(weaponData.sub_name, weapon_image_type[1]).get("image")
        weaponData2.sub_image = imageDB.get_weapon_image(weaponData2.sub_name, weapon_image_type[1]).get("image")
        # Special
        weaponData.special_image = imageDB.get_weapon_image(weaponData.special_name, weapon_image_type[2]).get("image")
        weaponData2.special_image = imageDB.get_weapon_image(weaponData2.special_name, weapon_image_type[2]).get(
            "image"
        )
        # Class
        weaponData.weapon_class_image = imageDB.get_weapon_image(weaponData.weapon_class, weapon_image_type[3]).get(
            "image"
        )
        weaponData2.weapon_class_image = imageDB.get_weapon_image(weaponData2.weapon_class, weapon_image_type[3]).get(
            "image"
        )
        # 添加
        weapon1.append(weaponData)
        weapon2.append(weaponData2)
    return weapon1, weapon2


# 取 图 信息
def get_stage_info(num_list=None, contest_match=None, rule_match=None):
    if num_list is None:
        num_list = [0]
    schedule = get_schedule_data()
    get_trans_data()
    # 竞赛 规则
    if contest_match is not None and contest_match != "":
        new_contest_match = dict_contest_trans[contest_match]
    else:
        new_contest_match = contest_match
    if rule_match is not None and rule_match != "":
        new_rule_match = dict_rule_trans[rule_match]
    else:
        new_rule_match = rule_match

    return schedule, num_list, new_contest_match, new_rule_match


if __name__ == "__main__":
    # get_stage_info().show()
    get_coop_info().show()
