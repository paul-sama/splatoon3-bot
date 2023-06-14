# import nonebot
import random
import re
import time

from nonebot import get_driver, logger
from nonebot import on_command, on_regex, on_startswith
from nonebot.adapters import Event
from nonebot.adapters import Bot

from nonebot.adapters.onebot.v11 import Bot as QQBot, Message
from nonebot.adapters.telegram import Bot as TGBot

from nonebot.adapters.telegram.message import File
from nonebot.adapters.onebot.v11.message import MessageSegment

from .config import Config
from .data_source import *
from .utils import *
from .imageProcesser import *

global_config = get_driver().config
config = Config(**global_config.dict())
# Response

matcher_select_stage = on_regex('[0-9]+图')
matcher_select_stage_mode_rule = on_regex('[0-9]+(区域|推塔|蛤蜊|抢鱼)(挑战|开放|X段|x段)')
matcher_select_stage_mode = on_regex('[0-9]+(挑战|开放|涂地|X段|x段)')
matcher_select_all_mode_rule = on_regex('全部(区域|推塔|蛤蜊|抢鱼)(挑战|开放|X段|x段)')
matcher_select_all_mode = on_regex('全部(挑战|开放|涂地|X段|x段)')
matcher_coop = on_command('工', block=True)
matcher_all_coop = on_command('全部工', aliases={'coop_schedule'}, block=True)
matcher_stage_group = on_command('图', block=True)
matcher_stage_group2 = on_command('图图', block=True)
matcher_stage_next1 = on_command('下图', block=True)
matcher_stage_next12 = on_command('下图图', block=True)
matcher_random_weapon = on_command('随机武器', block=True)



async def bot_send(bot: Bot, event: Event, **kwargs):
    img = kwargs.get('img')
    if not img:
        logger.info('img is None')
        msg = '好像没有符合要求的地图模式>_<'
        await bot.send(event, message=msg)
        return

    if isinstance(bot, QQBot):
        logger.info('QQBot 不发地图信息')
        return
        img = MessageSegment.image(file=img, cache=False)

        msg = ''
        if 'group' in event.get_event_name():
            user_id = str(event.get_user_id())
            msg = f"[CQ:at,qq={user_id}]"

        message = Message(msg) + Message(img)
        try:
            await bot.send(event, message=message)
        except Exception as e:
            logger.error(f'QQBot send error: {e}')

    elif isinstance(bot, TGBot):
        await bot.send(event, File.photo(img), reply_to_message_id=event.dict().get('message_id'))


@matcher_random_weapon.handle()
async def _(bot: Bot, event: Event):
    await bot_send(bot, event, img=get_random_weapon())


@matcher_select_all_mode.handle()
async def _(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text()
    msg = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    img = get_stage_info(msg, stage_mode=plain_text[-2:])
    await bot_send(bot, event, img=img)


@matcher_select_all_mode_rule.handle()
async def _(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text()
    msg = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    img = get_stage_info(msg, stage_mode=plain_text[-4:])
    await bot_send(bot, event, img=img)


@matcher_select_stage_mode_rule.handle()
async def _(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text()
    msg = list(set([int(x) for x in plain_text[:-4]]))
    msg.sort()
    img = get_stage_info(msg, stage_mode=plain_text[-4:])
    await bot_send(bot, event, img=img)


@matcher_select_stage_mode.handle()
async def _(bot: Bot, event: Event):
    plain_text = event.get_message().extract_plain_text()
    msg = list(set([int(x) for x in plain_text[:-2]]))
    msg.sort()
    img = get_stage_info(msg, stage_mode=plain_text[-2:])
    await bot_send(bot, event, img=img)


@matcher_select_stage.handle()
async def _(bot: Bot, event: Event):
    msg = list(set([int(x) for x in event.get_message().extract_plain_text()[:-1]]))
    msg.sort()
    img = get_stage_info(msg)
    await bot_send(bot, event, img=img)


@matcher_coop.handle()
async def _(bot: Bot, event: Event):
    res = get_coop_info(all=False)
    await bot_send(bot, event, img=res)

@matcher_all_coop.handle()
async def _(bot: Bot, event: Event):
    res = get_coop_info(all=True)
    await bot_send(bot, event, img=res)


@matcher_stage_group.handle()
async def _(bot: Bot, event: Event):
    img = get_stage_info()
    await bot_send(bot, event, img=img)

@matcher_stage_group2.handle()
async def _(bot: Bot, event: Event):
    img = get_stage_info([0, 1])
    await bot_send(bot, event, img=img)


@matcher_stage_next1.handle()
async def _(bot: Bot, event: Event):
    args = str(event.get_message()).strip()
    img = get_stage_info([1])
    await bot_send(bot, event, img=img)


@matcher_stage_next12.handle()
async def _(bot: Bot, event: Event):
    img = get_stage_info([1, 2])
    await bot_send(bot, event, img=img)
