import re

from nonebot import on_regex
from nonebot.adapters import Event
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.log import logger

from .static_data_getter import reload_weapon_info
from .image_processer import imageDB

matcher_admin = on_regex("^[\\\/\.。]?(重载武器数据|更新武器数据|清空图片缓存)$", priority=9, block=True, permission=SUPERUSER)


# 重载武器数据，包括：武器图片，副武器图片，大招图片，武器配置信息
@matcher_admin.handle()
async def _(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text().strip()
    err_msg = "执行失败，错误日志为: "
    logger.info('admin matcher: ' + plain_text)
    # 清空图片缓存
    if re.search("^清空图片缓存$", plain_text):
        msg = "数据库合成图片缓存数据已清空！"
        try:
            imageDB.clean_image_temp()
        except Exception as e:
            msg = err_msg + str(e)
        # 发送消息
        await bot.send(event, message=msg)
    elif re.search("^(重载武器数据|更新武器数据)$", plain_text):
        msg_start = "将开始重新爬取武器数据，此过程可能需要10min左右..."
        msg = "武器数据更新完成"
        await bot.send(event, message=msg_start)
        try:
            reload_weapon_info()
        except Exception as e:
            msg = err_msg + str(e)
        await bot.send(event, message=msg)
