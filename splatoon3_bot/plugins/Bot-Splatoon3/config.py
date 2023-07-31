from typing import List, Union

from nonebot import get_driver
from pydantic import BaseModel, validator


# 其他地方出现的类似 from .. import config，均是从 __init__.py 导入的 Config 实例
class Config(BaseModel):
    # 默认 proxy = None 表示不使用代理进行连接
    splatoon3_proxy_address: str = ""
    # 是否允许私聊消息回应，默认False
    # 该配置项仅影响 onebotV11，实践表明私聊消息过多会导致Bot频繁被风控
    splatoon3_permit_private: bool = True
    # 是否允许频道消息回应，默认False
    splatoon3_permit_channel: bool = False
    # 是否允许未知来源消息回应，默认False
    splatoon3_permit_unkown_src: bool = False
    # 指定回复模式，开启后将通过触发词的消息进行回复
    splatoon3_reply_mode: bool = True
    # 白名单，填写后黑名单失效
    splatoon3_whitelist: List[str] = []
    # 黑名单
    splatoon3_blacklist: List[str] = []

    @validator("splatoon3_whitelist")
    def check_whitelist(cls, v):
        if isinstance(v, List):
            return v
        raise ValueError("""白名单格式错误，参考格式为 ["23333","114514"]""")

    @validator("splatoon3_blacklist")
    def check_blacklist(cls, v):
        if isinstance(v, List):
            return v
        raise ValueError("""黑名单格式错误，参考格式为 ["23333","114514"]""")

    def verify_permission(self, uid: Union[str, int]):
        """消息来源权限校验"""
        if self.splatoon3_whitelist:
            return str(uid) in self.splatoon3_whitelist
        elif self.splatoon3_blacklist:
            return str(uid) not in self.splatoon3_blacklist
        else:
            return True


# 本地测试时由于不启动 driver，需要将下面三行注释并取消再下面两行的注释
driver = get_driver()
global_config = driver.config
plugin_config = Config.parse_obj(global_config)

# driver = None
# plugin_config = Config()
