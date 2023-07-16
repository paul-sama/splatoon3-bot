import re

from nonebot import on_regex
from nonebot.adapters import Event
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11 import Bot as QQBot, Message
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.telegram.message import File
from nonebot.log import logger

from .image import (
    get_save_temp_image,
    get_coop_stages_image,
    get_random_weapon_image,
    get_stages_image,
    get_weapon_info_test,
)
from .translation import dict_keyword_replace
from .image_processer import imageDB
from .utils import multiple_replace
from .data_source import get_screenshot
from .admin_matcher import matcher_admin

# 初始化插件时清空合成图片缓存表
imageDB.clean_image_temp()

# 图 触发器  正则内需要涵盖所有的同义词
matcher_stage_group = on_regex("^[\\\/\.。]?[0-9]*(全部)?下*图+$", priority=9, block=True)

# 对战 触发器
matcher_stage = on_regex(
    "^[\\\/\.。]?[0-9]*(全部)?下*(区域|推塔|抢塔|塔楼|蛤蜊|抢鱼|鱼虎|涂地|涂涂|挑战|真格|开放|组排|排排|pp|PP|X段|x段|X赛|x赛){1,2}$",
    priority=9,
    block=True,
)

# 打工 触发器
matcher_coop = on_regex(
    "^[\\\/\.。]?(全部)?(工|打工|coop_schedule|鲑鱼跑|bigrun|big run|团队打工)$",
    priority=9,
    block=True,
)

# 其他命令 触发器
matcher_else = on_regex("^[\\\/\.。]?(帮助|help|(随机武器).*|装备|衣服|祭典|活动)$", priority=9, block=True)


async def bot_send(bot: Bot, event: Event, **kwargs):
    img = kwargs.get('img')
    if not img:
        logger.info('img is None')
        msg = '好像没有符合要求的地图模式>_<'
        await bot.send(event, message=msg)
        return

    if isinstance(bot, QQBot):
        img = MessageSegment.image(file=img, cache=False)

        msg = ''
        if 'group' in event.get_event_name():
            msg = f"[CQ:reply,id={event.dict().get('message_id')}]"

            # logger.info('QQBot 群不发地图信息')
            # return

        message = Message(msg) + Message(img)
        try:
            await bot.send(event, message=message)
        except Exception as e:
            logger.warning(f'QQBot send error: {e}')

    elif isinstance(bot, TGBot):
        await bot.send(event, File.photo(img), reply_to_message_id=event.dict().get('message_id'))


# 图 触发器处理 二次判断正则前，已经进行了同义词替换，二次正则只需要判断最终词
@matcher_stage_group.handle()
async def _(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text().strip()
    # 触发关键词  同义文本替换
    plain_text = multiple_replace(plain_text, dict_keyword_replace)
    logger.info("同义文本替换后触发词为:" + plain_text + "\n")
    # 判断是否满足进一步正则
    num_list = []
    contest_match = None
    rule_match = None
    flag_match = False
    # 顺序 单图
    if re.search("^[0-9]+图$", plain_text):
        num_list = list(set([int(x) for x in plain_text[:-1]]))
        num_list.sort()
        flag_match = True
    elif re.search("^下{1,11}图$", plain_text):
        re_list = re.findall("下", plain_text)
        num_list = list(set([len(re_list)]))
        num_list.sort()
        flag_match = True
    # 多图
    elif re.search("^下?图{1,11}$", plain_text):
        re_list = re.findall("图", plain_text)
        lens = len(re_list)
        # 渲染太慢了，限制查询数量
        if lens > 5:
            lens = 5
        num_list = list(set([x for x in range(lens)]))
        num_list.sort()
        if "下" in plain_text:
            num_list.pop(0)
        flag_match = True
    elif re.search("^全部图*$", plain_text):
        # 渲染太慢了，限制查询数量
        num_list = [0, 1, 2, 3, 4, 5]
        flag_match = True
    # 如果有匹配
    if flag_match:
        # 传递函数指针
        func = get_stages_image
        # 获取图片
        img = get_save_temp_image(plain_text, func, num_list, contest_match, rule_match)
        # 发送消息
        await bot_send(bot, event, img=img)


# 对战 触发器处理
@matcher_stage.handle()
async def _(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text().strip()
    # 触发关键词  同义文本替换  同时替换.。\/ 等前缀触发词
    plain_text = multiple_replace(plain_text, dict_keyword_replace)
    logger.info("同义文本替换后触发词为:" + plain_text)
    # 判断是否满足进一步正则
    num_list = []
    contest_match = None
    rule_match = None
    flag_match = False
    # 双筛选  规则  竞赛
    if re.search("^[0-9]*(全部)?(区域|蛤蜊|塔楼|鱼虎)(挑战|开放|X段)$", plain_text):
        if "全部" in plain_text:
            num_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        else:
            if len(plain_text) == 2:
                num_list = [0]
            else:
                num_list = list(set([int(x) for x in plain_text[:-4]]))
                num_list.sort()
        stage_mode = plain_text[-4:]
        contest_match = stage_mode[2:]
        rule_match = stage_mode[:2]
        flag_match = True
    # 双筛选  竞赛  规则
    elif re.search("^[0-9]*(全部)?(挑战|开放|X段)(区域|蛤蜊|塔楼|鱼虎)$", plain_text):
        if "全部" in plain_text:
            num_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        else:
            if len(plain_text) == 2:
                num_list = [0]
            else:
                num_list = list(set([int(x) for x in plain_text[:-4]]))
                num_list.sort()
        stage_mode = plain_text[-4:]
        contest_match = stage_mode[:2]
        rule_match = stage_mode[2:]
        flag_match = True
    # 单筛选  竞赛
    elif re.search("^[0-9]*(全部)?(挑战|开放|X段|涂地)$", plain_text):
        if "全部" in plain_text:
            num_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        else:
            if len(plain_text) == 2:
                num_list = [0]
            else:
                num_list = list(set([int(x) for x in plain_text[:-2]]))
                num_list.sort()

        stage_mode = plain_text[-2:]
        contest_match = stage_mode
        rule_match = None
        flag_match = True
    # 单筛选 下 竞赛
    elif re.search("^下{1,11}(挑战|开放|X段|涂地)$", plain_text):
        re_list = re.findall("下", plain_text)
        lens = len(re_list)
        num_list = list(set([lens]))
        num_list.sort()
        stage_mode = plain_text[-2:]
        contest_match = stage_mode
        rule_match = None
        flag_match = True
    # 单筛选  模式
    elif re.search("^[0-9]*(全部)?(区域|蛤蜊|塔楼|鱼虎)$", plain_text):
        if "全部" in plain_text:
            num_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        else:
            if len(plain_text) == 2:
                num_list = [0]
            else:
                num_list = list(set([int(x) for x in plain_text[:-2]]))
                num_list.sort()
        stage_mode = plain_text[-2:]
        rule_match = stage_mode
        contest_match = None
        flag_match = True
    # 单筛选 下 模式
    elif re.search("^下{1,11}(区域|蛤蜊|塔楼|鱼虎)$", plain_text):
        re_list = re.findall("下", plain_text)
        lens = len(re_list)
        num_list = list(set([lens]))
        stage_mode = plain_text[-2:]
        contest_match = None
        rule_match = stage_mode
        flag_match = True

    # 如果有匹配
    if flag_match:
        # 传递函数指针
        func = get_stages_image
        # 获取图片
        img = get_save_temp_image(plain_text, func, num_list, contest_match, rule_match)
        # 发送消息
        await bot_send(bot, event, img=img)


# 打工 触发器处理
@matcher_coop.handle()
async def _(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text().strip()
    # 触发关键词  同义文本替换
    plain_text = multiple_replace(plain_text, dict_keyword_replace)
    logger.info("同义文本替换后触发词为:" + plain_text + "\n")
    # 判断是否满足进一步正则
    _all = False
    if "全部" in plain_text:
        _all = True
    # 传递函数指针
    func = get_coop_stages_image
    # 获取图片
    img = get_save_temp_image(plain_text, func, _all)
    # 发送消息
    await bot_send(bot, event, img=img)


# 其他命令 触发器处理
@matcher_else.handle()
async def _(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text().strip()
    # 触发关键词  同义文本替换
    plain_text = multiple_replace(plain_text, dict_keyword_replace)
    logger.info("同义文本替换后触发词为:" + plain_text + "\n")
    # 判断是否满足进一步正则
    # 随机武器
    if re.search("^随机武器.*$", plain_text):
        # 这个功能不能进行缓存，必须实时生成图
        # 测试数据库能否取到武器数据
        if not get_weapon_info_test():
            msg = "请机器人管理员先发送 更新武器数据 更新本地武器数据库后，才能使用随机武器功能"
            await bot_send(bot, event, message=msg)
        else:
            img = get_random_weapon_image(plain_text)
            # 发送消息
            await bot_send(bot, event, img=img)
    elif re.search("^祭典$", plain_text):
        # 获取祭典，网页图片中含有倒计时，不适合进行缓存
        # 速度较慢，可以考虑后续从 json 自行生成，后续的分支都是网页截图
        img = await get_screenshot(shot_url="https://splatoon3.ink/splatfests")
        await bot_send(bot, event, img=img)
    elif re.search("^活动$", plain_text):
        img = await get_screenshot(shot_url="https://splatoon3.ink/challenges")
        await bot_send(bot, event, img=img)
    elif re.search("^装备$", plain_text):
        img = await get_screenshot(shot_url="https://splatoon3.ink/gear")
        await bot_send(bot, event, img=img)
