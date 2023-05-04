#!/usr/bin/env python3

from nonebot import on_command, logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Bot as QQBot, Message, MessageSegment
from nonebot.adapters.telegram import Bot as TGBot
from nonebot.adapters.telegram.message import File
from nonebot.typing import T_State

from .inkbot import stage_handle, coop_handle, textmode_handle

@on_command("图",
            aliases={'下图', '下下图', '当', '当当', '当当当', '排', '排排', '排排排', '排排排排',
                     '下下下图', '图2', '下图2', '下下图2', '下下下图2'},
            priority=5, block=True).handle()
async def bot_stage_handle(bot: Bot, event: Event, state: T_State):
    tmp_file, msg = await stage_handle(bot, event, state)
    if isinstance(bot, TGBot):
        await bot.send(event, File.photo(tmp_file) + msg)
    elif isinstance(bot, QQBot):
        img = MessageSegment.image('file:///' + tmp_file)

        if 'group' in event.get_event_name():
            user_id = str(event.get_user_id())
            msg = f"[CQ:at,qq={user_id}]{msg}"

        message = Message(msg) + Message(img)
        await bot.send(event, message=message)


@on_command("工", aliases={'下工', '下下工', '下下下工', '工2'}, priority=5, block=True).handle()
async def bot_coop_handle(bot: Bot, event: Event, state: T_State):
    tmp_file, msg = await coop_handle(bot, event, state)
    if isinstance(bot, TGBot):
        await bot.send(event, File.photo(tmp_file) + msg)

    elif isinstance(bot, QQBot):
        img = MessageSegment.image('file:///' + tmp_file)

        if 'group' in event.get_event_name():
            user_id = str(event.get_user_id())
            msg = f"[CQ:at,qq={user_id}]{msg}"

        message = Message(msg) + Message(img)
        await bot.send(event, message=message)
