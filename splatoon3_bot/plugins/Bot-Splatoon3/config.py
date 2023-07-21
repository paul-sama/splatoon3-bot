from typing import List, Optional

from nonebot import get_driver
from pydantic import BaseModel


# 其他地方出现的类似 from .. import config，均是从 __init__.py 导入的 Config 实例
class Config(BaseModel):
    # 默认 proxy = None 表示不使用代理进行连接
    splatoon3_proxy_address: str = None
    # 是否允许私聊消息回应，默认允许
    # 该配置项仅影响 onebotV11，实践表明私聊消息过多会导致Bot频繁被风控
    splatoon3_permit_private: bool = True


# 本地测试时由于不启动 driver，需要将下面两行注释并取消再下一行的注释
global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)

# plugin_config = Config()
