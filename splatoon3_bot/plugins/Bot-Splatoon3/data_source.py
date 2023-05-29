import httpx
import json
import urllib3

from .utils import *
from .imageProcesser import get_stages, get_coop_stages, get_all_coop_stages

schedule_res = None
http = urllib3.PoolManager()


def check_expire_schedule(schedule):
    st = datetime.datetime.strptime(schedule['regularSchedules']['nodes'][0]['startTime'], '%Y-%m-%dT%H:%M:%SZ')
    ed = datetime.datetime.strptime(schedule['regularSchedules']['nodes'][0]['endTime'], '%Y-%m-%dT%H:%M:%SZ')
    nw = datetime.datetime.now() - datetime.timedelta(hours=8)
    if st < nw < ed:
        return False
    return True


def get_schedule():
    global schedule_res
    if schedule_res is None or check_expire_schedule(schedule_res):
        print('Re-get schedule')
        with httpx.Client() as client:
            result = client.get('https://splatoon3.ink/data/schedules.json')
            schedule_res = json.load(result)
            schedule_res = schedule_res['data']
            return schedule_res
    else:
        return schedule_res


def get_coop_info(all = False):
    def get_stage_image_info(sch):  # schedule[idx]
        return ImageInfo(sch['setting']['coopStage']['name'], sch['setting']['coopStage']['image']['url'])

    def get_weapon_image_info(sch):  # schedule[idx]
        return [ImageInfo(sch['setting']['weapons'][i]['name'], sch['setting']['weapons'][i]['image']['url']) for i in range(4)]

    def get_str_info(sch):
        startTime = time_converter_day(sch['startTime'])
        endTime = time_converter_day(sch['endTime'])
        return '{} - {}'.format(startTime, endTime)

    schedule = get_schedule()
    schedule = schedule['coopGroupingSchedule']['regularSchedules']['nodes']
    if not all:

        stage_first = get_stage_image_info(schedule[0])
        stage_second = get_stage_image_info(schedule[1])
        weapon_first = get_weapon_image_info(schedule[0])
        weapon_second = get_weapon_image_info(schedule[1])
        info_first = get_str_info(schedule[0])
        info_second = get_str_info(schedule[1])

        return get_coop_stages(stage_first, weapon_first, info_first, stage_second, weapon_second, info_second)
    else:
        stage = [get_stage_image_info(i) for i in schedule]
        weapon = [get_weapon_image_info(i) for i in schedule]
        info = [get_str_info(i) for i in schedule]

        return get_all_coop_stages(stage, weapon, info)




def get_stage_info(num_list=None, stage_mode=None):
    if num_list is None:
        num_list = [0]
    schedule = get_schedule()
    if stage_mode is not None:
        if len(stage_mode) == 2:
            return get_stages(schedule, num_list, map_contest[stage_mode[:2]])
        elif len(stage_mode) == 4:
            return get_stages(schedule, num_list, map_contest[stage_mode[2:]], map_rule[stage_mode[:2]])
        else:
            raise NameError()
    return get_stages(schedule, num_list)


if __name__ == '__main__':
    # get_stage_info().show()
    get_coop_info().show()
