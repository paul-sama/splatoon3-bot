from typing import Union

from nonebot.adapters.telegram.message import File
from nonebot.params import Depends, CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.rule import is_type
from nonebot import on_regex

# onebot11 协议
from nonebot.adapters.onebot.v11 import Bot as V11Bot
from nonebot.adapters.onebot.v11 import MessageEvent as V11MEvent
from nonebot.adapters.onebot.v11 import Message as V11Msg
from nonebot.adapters.onebot.v11 import MessageSegment as V11MsgSeg
from nonebot.adapters.onebot.v11 import PrivateMessageEvent as V11PMEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11GMEvent

# onebot12 协议
from nonebot.adapters.onebot.v12 import Bot as V12Bot
from nonebot.adapters.onebot.v12 import MessageEvent as V12MEvent
from nonebot.adapters.onebot.v12 import Message as V12Msg
from nonebot.adapters.onebot.v12 import MessageSegment as V12MsgSeg
from nonebot.adapters.onebot.v12 import ChannelMessageEvent as V12CMEvent
from nonebot.adapters.onebot.v12 import PrivateMessageEvent as V12PMEvent
from nonebot.adapters.onebot.v12 import GroupMessageEvent as V12GMEvent

# telegram 协议
from nonebot.adapters.telegram import Bot as TgBot
from nonebot.adapters.telegram.event import MessageEvent as TgEvent
from nonebot.adapters.telegram import MessageSegment as TgMsgSeg

from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER

from .image.image import *
from .image import image_to_base64
from .config import plugin_config
from .utils import dict_keyword_replace, multiple_replace
from .data import get_screenshot, reload_weapon_info, imageDB

# zhenxunbot框架当前使用的是2.0.0rc1版本nb2，对以下插件元信息缺少参数，需要删除usage后面的字段，才能正常加载
__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-splatoon3",
    description="一个基于nonebot2框架的splatoon3游戏日程查询插件",
    usage="发送 帮助 或 help 可查看详细指令\n",
    type="application",
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。
    homepage="https://github.com/Skyminers/Bot-Splatoon3",
    # 发布必填。
    supported_adapters={"~onebot.v11", "~onebot.v12", "~telegram"},
)

# 初始化插件时清空合成图片缓存表
imageDB.clean_image_temp()

# v11判断是否允许私聊
if plugin_config.splatoon3_permit_private:
    msg_rule = is_type(V11PMEvent, V11GMEvent, V12PMEvent, V12GMEvent, V12CMEvent, TgEvent)
else:
    msg_rule = is_type(V11GMEvent, V12GMEvent, V12CMEvent, TgEvent)

# 图 触发器  正则内需要涵盖所有的同义词
matcher_stage_group = on_regex("^[\\/.,，。]?[0-9]*(全部)?下*图+$", priority=9, block=True, rule=msg_rule)


# 图 触发器处理 二次判断正则前，已经进行了同义词替换，二次正则只需要判断最终词
@matcher_stage_group.handle()
async def _(
    bot: Union[V11Bot, V12Bot, TgBot],
    matcher: Matcher,
    event: Union[V11MEvent, V12MEvent, TgEvent],
):
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
        # set是为了去除重复数字
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
        await send_img(bot, event, matcher, img)


# 对战 触发器
matcher_stage = on_regex(
    "^[\\/.,，。]?[0-9]*(全部)?下*(区域|推塔|抢塔|塔楼|蛤蜊|抢鱼|鱼虎|涂地|涂涂|挑战|单排|真格|开放|组排|排排|pp|PP|X段|x段|X赛|x赛){1,2}$",
    priority=9,
    block=True,
    rule=msg_rule,
)


# 对战 触发器处理
@matcher_stage.handle()
async def _(
    bot: Union[V11Bot, V12Bot, TgBot],
    matcher: Matcher,
    event: Union[V11MEvent, V12MEvent, TgEvent],
):
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
        # set是为了去除重复数字
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
        # set是为了去除重复数字
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
        await send_img(bot, event, matcher, img)


# 打工 触发器
matcher_coop = on_regex("^[\\/.,，。]?(全部)?(工|打工|coop_schedule|鲑鱼跑|bigrun|big run|团队打工)$", priority=9, block=True, rule=msg_rule)


# 打工 触发器处理
@matcher_coop.handle()
async def _(
    bot: Union[V11Bot, V12Bot, TgBot],
    matcher: Matcher,
    event: Union[V11MEvent, V12MEvent, TgEvent],
):
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
    await send_img(bot, event, matcher, img)


# 其他命令 触发器
matcher_else = on_regex("^[\\/.,，。]?(帮助|help|(随机武器).*|装备|衣服|祭典|活动)$", priority=9, block=True, rule=msg_rule)


# 其他命令 触发器处理
@matcher_else.handle()
async def _(
    bot: Union[V11Bot, V12Bot, TgBot],
    matcher: Matcher,
    event: Union[V11MEvent, V12MEvent, TgEvent],
):
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
            await send_msg(bot, event, matcher, msg)
        else:
            img = image_to_base64(get_random_weapon_image(plain_text))
            # 发送消息
            await send_img(bot, event, matcher, img)
    elif re.search("^祭典$", plain_text):
        # 传递函数指针
        func = get_festival_image
        # 获取图片
        img = get_save_temp_image(plain_text, func)
        if img is None:
            msg = "近期没有任何祭典"
            await send_msg(bot, event, matcher, msg)
        else:
            # 发送图片
            await send_img(bot, event, matcher, img)
    elif re.search("^活动$", plain_text):
        # 传递函数指针
        func = get_events_image
        # 获取图片
        img = get_save_temp_image(plain_text, func)
        if img is None:
            msg = "近期没有任何活动比赛"
            await send_msg(bot, event, matcher, msg)
        else:
            # 发送图片
            await send_img(bot, event, matcher, img)

    elif re.search("^帮助$", plain_text):
        # 传递函数指针
        func = get_help_image
        # 获取图片
        img = get_save_temp_image(plain_text, func)
        # 发送图片
        await send_img(bot, event, matcher, img)
    elif re.search("^装备$", plain_text):
        img = await get_screenshot(shot_url="https://splatoon3.ink/gear")
        # 发送图片
        await send_img(bot, event, matcher, img)


matcher_admin = on_regex("^[\\/.,，。]?(重载武器数据|更新武器数据|清空图片缓存)$", priority=9, block=True, permission=SUPERUSER)


# 重载武器数据，包括：武器图片，副武器图片，大招图片，武器配置信息
@matcher_admin.handle()
async def _(
    bot: Union[V11Bot, V12Bot, TgBot],
    matcher: Matcher,
    event: Union[V11MEvent, V12MEvent, TgEvent],
):
    plain_text = event.get_message().extract_plain_text().strip()
    err_msg = "执行失败，错误日志为: "
    # 清空图片缓存
    if re.search("^清空图片缓存$", plain_text):
        msg = "数据库合成图片缓存数据已清空！"
        try:
            imageDB.clean_image_temp()
        except Exception as e:
            msg = err_msg + str(e)
        # 发送消息
        await send_msg(bot, event, matcher, msg)

    elif re.search("^(重载武器数据|更新武器数据)$", plain_text):
        msg_start = "将开始重新爬取武器数据，此过程可能需要10min左右,请稍等..."
        msg = "武器数据更新完成"
        await send_msg(bot, event, matcher, msg_start)
        try:
            await reload_weapon_info()
        except Exception as e:
            msg = err_msg + str(e) + "\n如果错误信息是timed out，不妨可以等会儿重新发送指令"
        await send_msg(bot, event, matcher, msg)


# 公用send_msg
async def send_msg(bot: Union[V11Bot, V12Bot, TgBot], event: Union[V11MEvent, V12MEvent, TgEvent], matcher, msg):
    # 指定回复模式
    reply_mode = plugin_config.splatoon3_reply_mode
    if isinstance(bot, V11Bot):
        await bot.send(event, message=V11MsgSeg.text(msg), reply_message=reply_mode)
    elif isinstance(bot, V12Bot):
        await bot.send(event, message=V12MsgSeg.text(msg), reply_message=reply_mode)
    elif isinstance(bot, TgBot):
        if reply_mode:
            await bot.send(event, msg, reply_to_message_id=event.dict().get("message_id"))
        else:
            await bot.send(event, msg)


# 公用send_img
async def send_img(bot: Union[V11Bot, V12Bot, TgBot], event: Union[V11MEvent, V12MEvent, TgEvent], matcher, img):
    # 指定回复模式
    reply_mode = plugin_config.splatoon3_reply_mode
    if isinstance(bot, V11Bot):

        try:
            group_id = (event.dict() or {}).get('group_id')
            if group_id:
                group_id = str(group_id)
                from ..splatoon3_bot.db_sqlite import model_get_map_group_id_list
                stop_group_id_lst = model_get_map_group_id_list()
                logger.debug(f'stop_group_id_lst: {stop_group_id_lst}')
                if stop_group_id_lst and group_id in stop_group_id_lst:
                    logger.debug(f'qq群 {group_id} 停用该查地图插件')
                    return

        except Exception as e:
            logger.warning(f"QQBot bot map error: {e}")

        try:
            await bot.send(event, message=V11MsgSeg.image(file=img, cache=False), reply_message=reply_mode)
        except Exception as e:
            logger.warning(f"QQBot send error: {e}")
    elif isinstance(bot, V12Bot):
        # onebot12协议需要先上传文件获取file_id后才能发送图片
        try:
            resp = await bot.upload_file(type="data", name="temp.png", data=img)
            file_id = resp["file_id"]
            if file_id:
                await bot.send(event, message=V12MsgSeg.image(file_id=file_id), reply_message=reply_mode)
        except Exception as e:
            logger.warning(f"QQBot send error: {e}")
    elif isinstance(bot, TgBot):
        if reply_mode:
            await bot.send(event, File.photo(img), reply_to_message_id=event.dict().get("message_id"))
        else:
            await bot.send(event, File.photo(img))


# # 根据不同onebot协议消息路径分别取用户id
# def get_user_id():
#     def dependency(bot: Union[V11Bot, V12Bot], event: Union[V11MEvent, V12MEvent]) -> str:
#         if isinstance(event, V11MEvent):
#             cid = f"{bot.self_id}_{event.message_type}_"
#         else:
#             cid = f"{bot.self_id}_{event.detail_type}_"
#
#         if isinstance(event, V11MsgSeg) or isinstance(event, V12MsgSeg):
#             cid += str(event.group_id)
#         elif isinstance(event, V12CMEvent):
#             cid += f"{event.guild_id}_{event.channel_id}"
#         else:
#             cid += str(event.user_id)
#         return cid
#
#     return Depends(dependency)
