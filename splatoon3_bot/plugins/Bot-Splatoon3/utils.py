import datetime
from multiprocessing import Lock

map_contest = {'涂地': 'Turf War', '挑战': 'Ranked Challenge', '开放': 'Ranked Open', 'X段': 'X Schedule', 'x段': 'X Schedule'}
map_rule = {'区域': 'AREA', '推塔': 'LOFT', '蛤蜊': 'CLAM', '抢鱼': 'GOAL'}

white_list = ['458482582', '792711635', '835723997', '578031026', '1607044636']

trans_dict = {
    'LOFT': '推塔模式',
    'CLAM': '蛤蜊模式',
    'GOAL': '抢鱼模式',
    'AREA': '区域模式',
    'TURF_WAR': '涂地模式'
}

# stage_names = ['Scorch Gorge', 'Eeltail Alley', 'Hagglefish Market', 'Hagglefish Market']


class ImageInfo:
    def __init__(self, name, url):
        self.name = name
        self.url = url


image_json_lock = Lock()


def time_converter(time_str):
    # convert time to UTC+8
    dt = datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
    dt += datetime.timedelta(hours=8)
    return datetime.datetime.strftime(dt, '%H:%M')


def time_converter_day(time_str):
    # convert time to UTC+8
    dt = datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
    dt += datetime.timedelta(hours=8)
    return datetime.datetime.strftime(dt, '%m-%d %H:%M')


def check_group_id(group_id):
    # if group_id == '616533832':
    #     return False
    return True


def trans(text):
    if text in trans_dict:
        return trans_dict[text]
    return text
