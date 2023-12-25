import nonebot
import sys

from nonebot import logger
from nonebot.adapters.kaiheila import Adapter as KaiheilaAdapter
from nonebot.adapters.telegram import Adapter as TelegramAdapter
from nonebot.adapters.onebot.v11 import Adapter as QQAdapter
from nonebot.adapters.onebot.v12 import Adapter as WXAdapter
from nonebot.log import logger_id, default_filter


# 移除 NoneBot 默认的日志处理器
logger.remove(logger_id)
# 添加新的日志处理器
logger.add(
    sys.stdout,
    level=0,
    diagnose=True,
    format="<g>{time:MM-DD HH:mm:ss}</g> [<lvl>{level:>7}</lvl>] <c><u>{name}.{module}:{line}</u></c> | {message}",
    filter=default_filter
)


# 初始化 NoneBot
nonebot.init()


# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(TelegramAdapter)
driver.register_adapter(QQAdapter)
driver.register_adapter(WXAdapter)
driver.register_adapter(KaiheilaAdapter)


# 在这里加载插件
nonebot.load_builtin_plugins("echo")  # 内置插件
nonebot.load_plugins("splatoon3_bot/plugins")  # 本地插件

nonebot.logger.add("logs/splatoon3-bot.log", level="DEBUG", encoding="utf-8")
nonebot.logger.add("logs/cron_job.log", filter=lambda record: "cron" in record["extra"])
nonebot.logger.add("logs/report.log", filter=lambda record: "report" in record["extra"])


if __name__ == "__main__":
    nonebot.run()
