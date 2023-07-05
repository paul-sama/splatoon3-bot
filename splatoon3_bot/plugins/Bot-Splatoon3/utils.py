import datetime
import cfscrape

# 背景 rgb颜色
dict_bg_rgb = {
    "Turf War": (24, 200, 26),
    "Ranked Challenge": (227, 68, 17),
    "Ranked Open": (24, 200, 26),
    "X Schedule": (14, 205, 147),
    "打工": (14, 203, 146),
    "活动": (223, 42, 119),
}


# cf get
def cf_http_get(url: str):
    # 实例化一个create_scraper对象
    scraper = cfscrape.create_scraper()
    # 请求报错，可以加上时延
    # scraper = cfscrape.create_scraper(delay = 6)
    # 获取网页内容
    res = scraper.get(url)
    return res


# 批量替换文本
def multiple_replace(text, _dict):
    for key in _dict:
        text = text.replace(key, _dict[key])
    return text


# 时间转换 月-日
def time_converter_yd(time_str):
    # convert time to UTC+8
    dt = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    dt += datetime.timedelta(hours=8)
    return datetime.datetime.strftime(dt, "%m.%d")


# 时间转换 时:分
def time_converter(time_str):
    # convert time to UTC+8
    dt = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    dt += datetime.timedelta(hours=8)
    return datetime.datetime.strftime(dt, "%H:%M")


# 时间转换 月-日 时:分
def time_converter_day(time_str):
    # convert time to UTC+8
    dt = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    dt += datetime.timedelta(hours=8)
    return datetime.datetime.strftime(dt, "%m-%d %H:%M")


# 获取年月日
def get_time_ymd():
    # convert time to UTC+8
    dt = datetime.datetime.now().strftime("%Y-%m-%d")
    return dt
