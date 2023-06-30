import datetime

from nonebot.log import logger
from .data_source import get_coop_info, get_stage_info, get_screenshot
from .imageProcesser import (
    get_coop_stages,
    imageDB,
    image_to_base64,
    get_stages,
    get_random_weapon,
)

from PIL import Image
import io

time_format_ymdh = "%Y-%m-%dT%H"


# 取 打工图片
def get_coop_stages_image(*args):
    all = args[0]
    # 获取数据
    stage, weapon, time, boss, mode = get_coop_info(all)
    # 绘制图片
    image = get_coop_stages(stage, weapon, time, boss, mode)
    return image


# 取 对战图片
def get_stages_image(*args):
    num_list = args[0]
    contest_match = args[1]
    rule_match = args[2]
    logger.info("num_list为:" + str(num_list))
    logger.info("contest_match为:" + str(contest_match))
    logger.info("rule_match为:" + str(rule_match))
    # 获取数据
    schedule, new_num_list, new_contest_match, new_rule_match = get_stage_info(
        num_list, contest_match, rule_match
    )
    # 绘制图片
    image = get_stages(schedule, new_num_list, new_contest_match, new_rule_match)
    return image


# 取 随机武器图片 不能进行缓存，这个需要实时生成
def get_random_weapon_image(*args):
    weapon1 = args[0]
    weapon2 = args[1]
    # 绘制图片
    image = get_random_weapon(weapon1, weapon2)
    return image_to_base64(image)


# 计算过期时间 字符串 精确度为 ymdh
def get_expire_time():
    # 计算过期时间
    time_now = datetime.datetime.now()
    time_now_h = time_now.hour
    # 计算过期时间字符串
    # 判断当前小时是奇数还是偶数
    expire_time: datetime
    if (time_now_h % 2) == 0:
        # 偶数
        expire_time = time_now + datetime.timedelta(hours=2)
    else:
        expire_time = time_now + datetime.timedelta(hours=1)
    expire_time_str = expire_time.strftime(time_format_ymdh).strip()
    return expire_time_str


# 向数据库新增或读取图片二进制  缓存图片
def get_save_temp_image(trigger_word, func, *args):
    res = imageDB.get_img_temp(trigger_word)
    image: bytes
    if not res:
        # 重新生成图片并写入
        image_data = func(*args)
        image = image_to_base64(image_data)
        if len(image) != 0:
            logger.info("[ImageDB] new temp image {}".format(trigger_word))
            imageDB.add_or_modify_IMAGE_TEMP(trigger_word, image, get_expire_time())
        return image
    else:
        # 判断时间是否过期
        expire_time = datetime.datetime.strptime(res[1], time_format_ymdh)
        time_now = datetime.datetime.now()
        if time_now > expire_time:
            # 重新生成图片并写入
            image_data = func(*args)
            image = image_to_base64(image_data)
            if len(image) != 0:
                logger.info("[ImageDB] update temp image {}".format(trigger_word))
                imageDB.add_or_modify_IMAGE_TEMP(trigger_word, image, get_expire_time())
            return image
        logger.info("数据库内存在时效范围内的缓存图片，将从数据库读取缓存图片")
        return image_to_base64(Image.open(io.BytesIO(res[0])))
