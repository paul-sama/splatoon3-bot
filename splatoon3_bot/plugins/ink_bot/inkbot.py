
# -*- coding: utf-8 -*-
# @Time    : 2021-09-12
# @Author  : beanslee(疾风)
# @FileName: qqbot.py
# @purpose: splatoon qq bot
# @qq group id   ：929116038


import os
import json,base64
import requests
import datetime
from datetime import datetime, timedelta
from io import BytesIO
import time
import uuid
import PIL.Image
import PIL.ImageFont
import PIL.ImageDraw
from .splatoon_data import weapons,stage,subweapons,specials,subweapon_path,game_types,friend_list,stage3,weapons3


import random
import nonebot
from nonebot import get_driver, on_command, on_keyword
from nonebot.adapters.telegram import Bot, Message, Event
from nonebot.adapters.telegram.message import File
from nonebot.typing import T_State
import socket

socket.setdefaulttimeout(20)

date =datetime.now().strftime('%Y-%m-%d')

base_path = os.path.abspath(os.path.join(__file__, os.pardir)) + '/'
tmp_path = base_path+'temp/'
img_path=base_path+'resource/'
img_path_sub=base_path+'resource/subspe/'


counter=0
gamemode_rule_name ={'Clam Blitz':'蛤蜊','Tower Control':'占塔','Splat Zones':'区域','Rainmaker':'抢鱼','Turf War':'涂地'}


def get_counter(now ):
    global counter
    global date
    if date == now:
       counter += 1
    else:
    	 date =  datetime.now().strftime('%Y-%m-%d')
    	 counter=1

    return counter

def random_id(rtype):
 if rtype == 'wep':
   r= int(random.choice(list(weapons.keys())))
   if r<0:
     r=random_id('wep')
   else:
     return r
 elif rtype =='map':
  r=(random.choice(list(stage.keys())))
  if r.isdigit():
  	return r
  else:
  	r=random_id('map')
 else:
  pass

 return r


def img_to_b64(pic: PIL.Image.Image):
    buf = BytesIO()

    pic.save(buf, format="PNG")
    base64_str = base64.b64encode(buf.getbuffer()).decode()
    return "base64://" + base64_str



def circle_corner(img, radii):
    # 画圆（用于分离4个角）
    circle = PIL.Image.new('L', (radii * 2, radii * 2), 0)  # 创建黑色方形
    # circle.save('1.jpg','JPEG',qulity=100)
    draw = PIL.ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 黑色方形内切白色圆形
    # circle.save('2.jpg','JPEG',qulity=100)
    img = img.convert("RGBA")
    w, h = img.size
    alpha = PIL.Image.new('L', img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)),(w - radii, 0))  # 右上角
    alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)),(w - radii, h - radii))  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)),(0, h - radii))  # 左下角
    img.putalpha(alpha)		# 白色区域透明可见，黑色区域不可见
    return img

def merge_image(base_img,tmp_img,img_x,img_y,scale):

  #加载底图
  #base_img = Image.open(u'C:\\download\\games\\bg1.png')
  #加载需要P上去的图片
  #tmp_img = Image.open(u'C:\\download\\games\\b.png')
  #这里可以选择一块区域或者整张图片
  region = tmp_img

  width = int(region.size[0]*scale)
  height = int(region.size[1]*scale)
  region = region.resize((width, height), PIL.Image.ANTIALIAS)
  base_img = base_img.convert("RGBA")
  region = region.convert("RGBA")
  #透明png不变黑白背景，需要加第三个参数,jpg和png不能直接合并
  base_img.paste(region, (img_x,img_y),region)
  return base_img


async def stage_handle(bot: Bot, event: Event,state: T_State):
    #参数
    # keyword = str(event.get_message()).strip()
    #print('开始受理请求')
    starttime = datetime.now()
    keyword=state['_prefix']['command'][0]
    # user = str(event.user_id)
    user = ''
    # at_ = "[CQ:at,qq={}]".format(user)
    at_ = ''
    GameURL = 'https://splatoon2.ink/data/schedules.json'
    if keyword =='图' or keyword == '当' or keyword == '排' or keyword == '图2':
        times=0
    elif keyword =='下图' or keyword == '当当' or keyword == '排排' or keyword =='下图2':
        times=1
    elif keyword == '下下图' or keyword == '当当当' or keyword == '排排排' or keyword =='下下图2':
        times=2
    elif keyword == '下下下图' or keyword =='下下下图2':
         times=3
    else:
        times=3

    if '2' in keyword:
        GameURL = 'https://splatoon2.ink/data/schedules.json'
    else:
        GameURL = 'https://splatoon3.ink/data/schedules.json'

    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    header= { 'User-Agent' : user_agent }
    #每次实时获取数据
    GameMode = requests.get(GameURL,headers=header).json()

    #使用文件方式读取（可以1小时异步更新一次）
    #with open('E:\\game\\bot\\qqbot\\inkbot\\src\\plugins\\schedule.json','r',encoding='utf8')as fp:
    #  GameMode = json.load(fp)
    #windows本地默认有时差问题，美国虚拟机没有
    #now = datetime.utcnow()
    now = datetime.now()


    game_file=GameMode
    if '2' in keyword:
        Map1R, Map2R = stage[game_file['regular'][times]['stage_a']['id']]['name'], stage[game_file['regular'][times]['stage_b']['id']]['name']
        GameModeR = gamemode_rule_name[game_file['regular'][times]['rule']['name']]
        StartTimeR, EndTimeR = time.strftime("%H{h}",time.localtime(float(game_file['regular'][times]['start_time']))).format(h='时'),time.strftime("%H{h}",time.localtime(float(game_file['regular'][times]['end_time']))).format(h='时')
        Map1S, Map2S = stage[game_file['gachi'][times]['stage_a']['id']]['name'], stage[game_file['gachi'][times]['stage_b']['id']]['name']
        GameModeS = gamemode_rule_name[game_file['gachi'][times]['rule']['name']]
        if (len(GameModeS)) == 2:
            GameModeS=GameModeS[0]+'\n'+GameModeS[1]
        else:
            GameModeS='\n'+GameModeS[0]
        StartTimeS, EndTimeS = time.strftime("%H{h}",time.localtime(float(game_file['gachi'][times]['start_time']))).format(h='时'),time.strftime("%H{h}",time.localtime(float(game_file['gachi'][times]['end_time']))).format(h='时')
        Map1L, Map2L = stage[game_file['league'][times]['stage_a']['id']]['name'], stage[game_file['league'][times]['stage_b']['id']]['name']
        GameModeL = gamemode_rule_name[game_file['league'][times]['rule']['name']]
        if (len(GameModeL)) == 2:
            GameModeL=GameModeL[0]+'\n'+GameModeL[1]
        else:
            GameModeL='\n'+GameModeL[0]
        StartTimeL, EndTimeL = time.strftime("%H{h}",time.localtime(float(game_file['league'][times]['start_time']))).format(h='时'),time.strftime("%H{h}",time.localtime(float(game_file['league'][times]['end_time']))).format(h='时')
    else:
        try:
            Map1R = stage3[str(game_file['data']['regularSchedules']['nodes'][times]['regularMatchSetting']['vsStages'][0]['vsStageId'])]['cname']
            Map2R = stage3[str(game_file['data']['regularSchedules']['nodes'][times]['regularMatchSetting']['vsStages'][1]['vsStageId'])]['cname']

            GameModeR = '涂地'
            StartTimeR = str((datetime.strptime(game_file['data']['regularSchedules']['nodes'][times]['startTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).hour) + '时'
            EndTimeR =   str((datetime.strptime(game_file['data']['regularSchedules']['nodes'][times]['endTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).hour) + '时'


            Map1S = stage3[str(game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][0]['vsStages'][0]['vsStageId'])]['cname']
            Map2S = stage3[str(game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][0]['vsStages'][1]['vsStageId'])]['cname']
            GameModeS = gamemode_rule_name[ game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][0]['vsRule']['name']]
            if (len(GameModeS)) == 2:
                GameModeS=GameModeS[0]+'\n'+GameModeS[1]
            else:
                GameModeS='\n'+GameModeS[0]

            StartTimeS = str((datetime.strptime(game_file['data']['bankaraSchedules']['nodes'][times]['startTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).hour) + '时'
            EndTimeS =   str((datetime.strptime(game_file['data']['bankaraSchedules']['nodes'][times]['endTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).hour) + '时'
            Map1L = stage3[str(game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][1]['vsStages'][0]['vsStageId'])]['cname']
            Map2L = stage3[str(game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][1]['vsStages'][1]['vsStageId'])]['cname']

            GameModeL = gamemode_rule_name[ game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][1]['vsRule']['name']]
            GameMode = GameModeL
            if (len(GameModeL)) == 2:
                GameModeL=GameModeL[0]+'\n'+GameModeL[1]
            else:
                GameModeL='\n'+GameModeL[0]
            StartTimeL, EndTimeL = StartTimeS, EndTimeS
            StartTimeX = str((datetime.strptime(game_file['data']['xSchedules']['nodes'][times]['startTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).hour) + '时'
            EndTimeX =   str((datetime.strptime(game_file['data']['xSchedules']['nodes'][times]['endTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).hour) + '时'
            Map1X = stage3[str(game_file['data']['xSchedules']['nodes'][times]['xMatchSetting']['vsStages'][0]['vsStageId'])]['cname']
            Map2X = stage3[str(game_file['data']['xSchedules']['nodes'][times]['xMatchSetting']['vsStages'][1]['vsStageId'])]['cname']

            GameModeX = gamemode_rule_name[ game_file['data']['xSchedules']['nodes'][times]['xMatchSetting']['vsRule']['name']]
            GameMode = GameModeX
            if (len(GameModeX)) == 2:
                GameModeX=GameModeX[0]+'\n'+GameModeX[1]
            else:
                GameModeX='\n'+GameModeX[0]
            StartTimeX, EndTimeX = StartTimeX, EndTimeX
        except Exception as e:
            pass
            Map1R = stage3[str(game_file['data']['festSchedules']['nodes'][times]['festMatchSetting']['vsStages'][0]['vsStageId'])]['cname']
            Map2R = stage3[str(game_file['data']['festSchedules']['nodes'][times]['festMatchSetting']['vsStages'][1]['vsStageId'])]['cname']

            GameModeR = '涂地'
            StartTimeR = str((datetime.strptime(game_file['data']['festSchedules']['nodes'][times]['startTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).hour) + '时'
            EndTimeR =   str((datetime.strptime(game_file['data']['festSchedules']['nodes'][times]['endTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).hour) + '时'


    global img_path

    base_img = PIL.Image.open(img_path+'misc/bg3.jpg')
    radii=20
    base_img = circle_corner(base_img, radii)
    base_sep=8
    scale=0.8
    base_xx=100
    base_yy=15
    endtime = datetime.now()
    #print('1:',(endtime-starttime).seconds)
    starttime = endtime
    if '2' in keyword:
        tmp_img = PIL.Image.open(img_path+stage[game_file['regular'][times]['stage_a']['id']]['image'])
        base_img=merge_image(base_img,tmp_img,base_xx,base_yy,scale)
        base_xx_incr=base_xx+int(tmp_img.size[0]*scale)+base_sep
        tmp_img = PIL.Image.open(img_path+stage[game_file['regular'][times]['stage_b']['id']]['image'])
        base_img=merge_image(base_img,tmp_img,base_xx_incr,base_yy,scale)
        base_yy_incr=int(tmp_img.size[1]*scale)+base_sep+base_yy
        tmp_img=PIL.Image.open(img_path+'mode/regular.png')
        base_img=merge_image(base_img,tmp_img,base_xx_incr-35,int(base_yy_incr/2)-20,0.5)

        tmp_img = PIL.Image.open(img_path+stage[game_file['gachi'][times]['stage_a']['id']]['image'])
        base_img=merge_image(base_img,tmp_img,base_xx,base_yy_incr,scale)
        tmp_img = PIL.Image.open(img_path+stage[game_file['gachi'][times]['stage_b']['id']]['image'])
        base_img=merge_image(base_img,tmp_img,base_xx_incr,base_yy_incr,scale)
        tmp_img=PIL.Image.open(img_path+'mode/rank.png')
        base_img=merge_image(base_img,tmp_img,int(base_xx_incr)-35,int(base_yy_incr)+30,0.5)

        tmp_img = PIL.Image.open(img_path+stage[game_file['league'][times]['stage_a']['id']]['image'])
        base_img=merge_image(base_img,tmp_img,base_xx,int(base_yy_incr*1.5)+65,scale)
        tmp_img = PIL.Image.open(img_path+stage[game_file['league'][times]['stage_b']['id']]['image'])
        base_img=merge_image(base_img,tmp_img,base_xx_incr,int(base_yy_incr*1.5)+65,scale)
        tmp_img=PIL.Image.open(img_path+'mode/league1.png')
        base_img=merge_image(base_img,tmp_img,int(base_xx_incr)-35,int(base_yy_incr*2)+20,0.5)
        draw = PIL.ImageDraw.Draw(base_img)
        font = PIL.ImageFont.truetype(img_path+"font/msyh.ttc", 45)
        draw.text((30,20 ), f"涂\n地", (255, 255, 255), font=font)
        draw.text((30,170), GameModeS, (255, 255, 255), font=font)
        draw.text((30,310), GameModeL, (255, 255, 255), font=font)
        base_img=base_img.resize((int(base_img.size[0]*0.8), int(base_img.size[1]*0.8)),PIL.Image.ANTIALIAS)
    else:
        try:
            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['regularSchedules']['nodes'][times]['regularMatchSetting']['vsStages'][0]['vsStageId'])]['image'])
            base_img=merge_image(base_img,tmp_img,base_xx,base_yy,scale)
            base_xx_incr=base_xx+int(tmp_img.size[0]*scale)+base_sep
            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['regularSchedules']['nodes'][times]['regularMatchSetting']['vsStages'][1]['vsStageId'])]['image'],)
            base_img=merge_image(base_img,tmp_img,base_xx_incr,base_yy,scale)
            base_yy_incr=int(tmp_img.size[1]*scale)+base_sep+base_yy
            tmp_img=PIL.Image.open(img_path+'mode/regular.png')
            base_img=merge_image(base_img,tmp_img,base_xx_incr-35,int(base_yy_incr/2)-20,0.5)

            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][0]['vsStages'][0]['vsStageId'])]['image'])
            base_img=merge_image(base_img,tmp_img,base_xx,base_yy_incr,scale)
            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][0]['vsStages'][1]['vsStageId'])]['image'])
            base_img=merge_image(base_img,tmp_img,base_xx_incr,base_yy_incr,scale)
            tmp_img=PIL.Image.open(img_path+'mode/rank.png')
            base_img=merge_image(base_img,tmp_img,int(base_xx_incr)-35,int(base_yy_incr)+30,0.5)

            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][1]['vsStages'][0]['vsStageId'])]['image'])
            base_img=merge_image(base_img,tmp_img,base_xx,int(base_yy_incr*1.5)+65,scale)
            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['bankaraSchedules']['nodes'][times]['bankaraMatchSettings'][1]['vsStages'][1]['vsStageId'])]['image'])
            base_img=merge_image(base_img,tmp_img,base_xx_incr,int(base_yy_incr*1.5)+65,scale)
            tmp_img=PIL.Image.open(img_path+'mode/league1.png')
            base_img=merge_image(base_img,tmp_img,int(base_xx_incr)-35,int(base_yy_incr*2)+20,0.5)

            #x mode
            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['xSchedules']['nodes'][times]['xMatchSetting']['vsStages'][0]['vsStageId'])]['image'])
            base_img=merge_image(base_img,tmp_img,base_xx,448,scale)
            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['xSchedules']['nodes'][times]['xMatchSetting']['vsStages'][1]['vsStageId'])]['image'])
            base_img=merge_image(base_img,tmp_img,base_xx_incr,448,scale)
            tmp_img=PIL.Image.open(img_path+'mode/x.png')
            base_img=merge_image(base_img,tmp_img,int(base_xx_incr)-35,490,0.5)

            draw = PIL.ImageDraw.Draw(base_img)
            font = PIL.ImageFont.truetype(img_path+"font/msyh.ttc", 45)
            draw.text((30,20 ), f"涂\n地", (255, 255, 255), font=font)
            draw.text((30,170), GameModeS, (255, 255, 255), font=font)
            draw.text((30,310), GameModeL, (255, 255, 255), font=font)
            draw.text((30,460), GameModeX, (255, 255, 255), font=font)
            base_img=base_img.resize((int(base_img.size[0]*0.8), int(base_img.size[1]*0.8)),PIL.Image.ANTIALIAS)
        except Exception as e:
            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['festSchedules']['nodes'][times]['festMatchSetting']['vsStages'][0]['vsStageId'])]['image'])
            base_img=merge_image(base_img,tmp_img,base_xx,base_yy,scale)
            base_xx_incr=base_xx+int(tmp_img.size[0]*scale)+base_sep
            tmp_img = PIL.Image.open(img_path+stage3[str(game_file['data']['festSchedules']['nodes'][times]['festMatchSetting']['vsStages'][1]['vsStageId'])]['image'],)
            base_img=merge_image(base_img,tmp_img,base_xx_incr,base_yy,scale)
            base_yy_incr=int(tmp_img.size[1]*scale)+base_sep+base_yy
            tmp_img=PIL.Image.open(img_path+'mode/regular.png')
            base_img=merge_image(base_img,tmp_img,base_xx_incr-35,int(base_yy_incr/2)-20,0.5)
            font = PIL.ImageFont.truetype(img_path+"font/msyh.ttc", 45)
            draw = PIL.ImageDraw.Draw(base_img)
            draw.text((30,20 ), f"祭\n典", (255, 255, 255), font=font)
            base_img=base_img.resize((int(base_img.size[0]*0.8), int(base_img.size[1]*0.8)),PIL.Image.ANTIALIAS)
            base_img = base_img.crop((0,0,base_img.size[0],base_img.size[1]/2.5)) #

    tmp_file = tmp_path+uuid.uuid4().hex+'.jpg'
    rgb_img = base_img.convert('RGB')
    rgb_img.save(tmp_file,compress_level=9)

    msg = '所处时段:'+ StartTimeR+ '-' + EndTimeR
    return tmp_file, msg




async def coop_handle(bot: Bot, event: Event,state: T_State):
    keyword=state['_prefix']['command'][0]
    user = ''
    global img_path
    at_ = ''

    if keyword =='工' or keyword == '工2':
        times=0
    elif keyword =='下工':
        times=1
    elif keyword == '下下工':
        times=2
    elif keyword == '下下下工':
         times=3
    else:
        times=3
    if '2' in keyword:
        GameURL = 'https://splatoon2.ink/data/coop-schedules.json'
    else:
        GameURL = 'https://splatoon3.ink/data/schedules.json'
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    header= { 'User-Agent' : user_agent }
    GameMode =(requests.get(GameURL,headers=header)).json()
    salmon_file = GameMode

    #with open('E:\\game\\bot\\qqbot\\inkbot\\src\\plugins\\coop_schedules.json','r',encoding='utf8')as fp:
    #  salmon_file = json.load(fp)
    #windows本地默认有时差问题，美国虚拟机没有
    #now = datetime.utcnow()
    now = datetime.now()

    base_img = PIL.Image.open(img_path+ 'misc/bgx.jpg').convert("RGBA")
    radii=20
    base_sep=8
    scale=1.5
    base_xx=20
    base_yy=60
    draw = PIL.ImageDraw.Draw(base_img)
    font = PIL.ImageFont.truetype(img_path+"font/msyh.ttc", 20)
    timecol=30
    if '2' in keyword:

        now = datetime.now()
        #不使用utc
        if now<=datetime.fromtimestamp(float(salmon_file['details'][0]['start_time'])):
            work_status='距下一开工时段还有:\n'
            time_delay=(datetime.fromtimestamp(float(salmon_file['details'][0]['start_time']))-now)
        else:
            work_status='剩余时间:'
            next_time=datetime.fromtimestamp(float(salmon_file['details'][0]['end_time']))
            time_delay= (next_time-now)

        hours,r=divmod((time_delay).seconds,3600)
        minutes,seconds=divmod(r,60)
        days=time_delay.days
        if days>0:
            days=str(days)+'天'
        else:
            days=''
        if hours>0:
            hours=str(hours)+'时'
        else:
            hours=''
        if minutes>0:
            minutes=str(minutes)+'分'
        else:
            minutes=''
        if seconds>0:
            seconds=str(seconds)+'秒'
        else:
            seconds=''
        #draw.text((base_xx,15), '当前时段剩余时间:'+days+hours+minutes+seconds, (255, 255, 255), font=font)

        #for i in  json.loads(json.dumps(json.loads(rsl.text)))['details']:
        #linux bug on linux @210925
        for i in json.loads(json.dumps(salmon_file))['details']:
            stime,etime=time.strftime("%m{m}%d{d}%H{h}",time.localtime(float(i['start_time']))).format(m='月',d='日',h='时'),time.strftime("%m{m}%d{d}%H{h}",time.localtime(float(i['end_time']))).format(m='月',d='日',h='时')

            draw.text((base_xx,timecol), stime +' - '+ etime, (255, 255, 255), font=font)
            tmp_img = PIL.Image.open(img_path+stage[i['stage']['name']]['image'])
            base_x = int(tmp_img.size[0]*scale)+base_sep*2
            base_y = int(tmp_img.size[1]*scale)+base_sep*2
            timecol=base_y+base_yy
        for i in  json.loads(json.dumps(salmon_file))['details']:

            #print (type(i),i['start_time'],i['end_time'],stage[i['stage']['name']]['name'][3:])

            stime,etime=time.strftime("%m{m}%d{d}%H{h}",time.localtime(float(i['start_time']))).format(m='月',d='日',h='时'),time.strftime("%m{m}%d{d}%H{h}",time.localtime(float(i['end_time']))).format(m='月',d='日',h='时')
        # draw.text((base_xx,timecol), stime+' - '+etime, (255, 255, 255), font=font)
            tmp_img = PIL.Image.open(img_path+stage[i['stage']['name']]['image'])
            base_x = int(tmp_img.size[0]*scale)+base_sep*2
            base_y = int(tmp_img.size[1]*scale)+base_sep*2
            timecol=base_y+base_yy

            #地图图片位置
            base_img = merge_image(base_img,tmp_img,base_xx,base_yy,scale)
            #武器初始位置=地图位置+空格
            base_wep_y = base_yy
            base_wep_x = base_x+base_xx
            k=0
            #print (base_img.size)
            #linux bug : weapon chinese name can not draw
            for j in i['weapons']:

                if 'weapon' in j.keys():
                    tmp_img = PIL.Image.open(img_path+weapons[j['weapon']['id']]['image'])
                    draw.text((base_wep_x+base_sep,base_wep_y+int(tmp_img.size[1]*0.5)-base_sep), weapons[j['weapon']['id']]['cn'], (255, 255, 255), font=font)
                else:
                    tmp_img = PIL.Image.open(img_path+weapons[j['id']]['image'])
                    draw.text((base_wep_x+base_sep,base_wep_y+int(tmp_img.size[1]*0.5)-base_sep), weapons[j['id']]['cn'], (255, 255, 255), font=font)
                #print(weapons[j['id']]['cn'])
                base_img=merge_image(base_img,tmp_img,base_wep_x,base_wep_y,0.5)
                #draw.text((base_wep_x+base_sep,base_wep_y+int(tmp_img.size[1]*0.5)-base_sep), weapons[j['weapon']['id']]['cn'], (255, 255, 255), font=font)
                k=k+1
                if k==2:
                    base_wep_y=base_wep_y+int(tmp_img.size[1]*0.5)+base_sep*4
                    base_wep_x=base_x+base_xx+base_sep
                elif k==1 or k==3:
                    #base_wep_y=base_wep_y+50
                    base_wep_x=base_wep_x+int(tmp_img.size[0]*0.5)+base_sep*3
            base_yy = base_yy+base_y+base_sep*3
            #base_yy=int(tmp_img.size[1]*0.7)+base_sep+base_yy
        base_img = base_img.crop((0,0,base_img.size[0]-60,base_img.size[1])) #
        base_img = circle_corner(base_img, radii)
        tmp_file = tmp_path+uuid.uuid4().hex+'.jpg'
        rgb_img = base_img.convert('RGB')
        rgb_img.save(tmp_file,compress_level=9)
        #base_img.save(tmp_file,quality =60,subsampling = 0)
        #imgs = f"[CQ:image,file={img_to_b64(base_img)}]"

        #
        img = stage[salmon_file['details'][0]['stage']['name']]['image']
        #img = url+img



        msg = at_+'\n打工安排:\n'+ work_status+days+hours+minutes
        msg = Message(msg)
    else:
        Map = stage3[str(salmon_file['data']['coopGroupingSchedule']['regularSchedules']['nodes'][times]['setting']['coopStage']['name'])]['image']
        MapName = stage3[str(salmon_file['data']['coopGroupingSchedule']['regularSchedules']['nodes'][times]['setting']['coopStage']['name'])]['name']

        stime = (datetime.strptime(salmon_file['data']['coopGroupingSchedule']['regularSchedules']['nodes'][times]['startTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).strftime("%d日%H时")
        etime = (datetime.strptime(salmon_file['data']['coopGroupingSchedule']['regularSchedules']['nodes'][times]['endTime'],"%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)).strftime("%d日%H时")
        #draw.text((base_xx,timecol-10), stime +' - '+ etime, (255, 255, 255), font=font)
        font = PIL.ImageFont.truetype(img_path+"font/msyh.ttc", 40)
        draw.text((base_xx,timecol-20), MapName, (255, 255, 255), font=font)



        tmp_img = PIL.Image.open(img_path+Map)
        base_x = int(tmp_img.size[0]*scale)+base_sep*2
        base_y = int(tmp_img.size[1]*scale)+base_sep*2
        timecol=base_y+base_yy

        #draw.text((base_xx,timecol), stime +' - '+ etime, (255, 255, 255), font=font)
        #draw.text((base_xx,timecol-10), MapName, (255, 255, 255), font=font)
        #地图图片位置
        base_img = merge_image(base_img,tmp_img,base_xx,base_yy,scale)

        #武器初始位置=地图位置+空格
        base_wep_y = base_yy
        base_wep_x = base_x+base_xx
        k=0

        for j in salmon_file['data']['coopGroupingSchedule']['regularSchedules']['nodes'][times]['setting']['weapons']:
            tmp_img = PIL.Image.open(img_path+'weapons/'+weapons3[j['name']]['wimg'])
            if j['name']=='Random':
              wep_rate=1
            else:
              wep_rate=0.25
            base_img=merge_image(base_img,tmp_img,base_wep_x,base_wep_y,0.35)
            k=k+1
            if k==2:
                base_wep_y=base_wep_y+int(tmp_img.size[1]*wep_rate)+base_sep*2
                base_wep_x=base_x+base_xx+base_sep
            elif k==1 or k==3:
                base_wep_x=base_wep_x+int(tmp_img.size[0]*wep_rate)+base_sep*4
        base_img = base_img.crop((0,0,base_img.size[0]-60,base_img.size[1]/2)) #
        base_img = circle_corner(base_img, radii)
        tmp_file = tmp_path+uuid.uuid4().hex+'.jpg'
        rgb_img = base_img.convert('RGB')
        rgb_img.save(tmp_file,compress_level=9)
        msg = at_+'\n打工安排:\n'+stime+'-'+etime
        msg = Message(msg)

    return tmp_file, msg


async def textmode_handle(bot: Bot, event: Event,state: T_State):
    #参数
    # keyword = str(event.get_message()).strip()
    #print('开始受理请求')
    starttime = datetime.now()
    keyword=state['_prefix']['command'][0]
    # user = str(event.user_id)
    at_ = ''
    if keyword =='文':
        times=0
    elif keyword =='下文':
        times=1
    elif keyword == '下下文':
        times=2
    else:
        times=3
    GameURL = 'https://splatoon2.ink/data/schedules.json'
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    header= { 'User-Agent' : user_agent }
    #每次实时获取数据
    GameMode = requests.get(GameURL,headers=header).json()

    now = datetime.now()


    game_file=GameMode

    Map1R, Map2R = stage[game_file['regular'][times]['stage_a']['id']]['name'], stage[game_file['regular'][times]['stage_b']['id']]['name']
    GameModeR = gamemode_rule_name[game_file['regular'][times]['rule']['name']]
    StartTimeR, EndTimeR = time.strftime("%H{h}",time.localtime(float(game_file['regular'][times]['start_time']))).format(h='时'),time.strftime("%H{h}",time.localtime(float(game_file['regular'][times]['end_time']))).format(h='时')
    Map1S, Map2S = stage[game_file['gachi'][times]['stage_a']['id']]['name'], stage[game_file['gachi'][times]['stage_b']['id']]['name']
    GameModeS = gamemode_rule_name[game_file['gachi'][times]['rule']['name']]
    if (len(GameModeS)) == 2:
        GameModeS=GameModeS[0]+GameModeS[1]
    else:
        GameModeS=''+GameModeS[0]
    StartTimeS, EndTimeS = time.strftime("%H{h}",time.localtime(float(game_file['gachi'][times]['start_time']))).format(h='时'),time.strftime("%H{h}",time.localtime(float(game_file['gachi'][times]['end_time']))).format(h='时')
    Map1L, Map2L = stage[game_file['league'][times]['stage_a']['id']]['name'], stage[game_file['league'][times]['stage_b']['id']]['name']
    GameModeL = gamemode_rule_name[game_file['league'][times]['rule']['name']]
    if (len(GameModeL)) == 2:
        GameModeL=GameModeL[0]+GameModeL[1]
    else:
        GameModeL=GameModeL[0]
    StartTimeL, EndTimeL = time.strftime("%H{h}",time.localtime(float(game_file['league'][times]['start_time']))).format(h='时'),time.strftime("%H{h}",time.localtime(float(game_file['league'][times]['end_time']))).format(h='时')



    msg = at_+'\n所处时段:'+ StartTimeR+ '-' + EndTimeR+'                             \n涂地:'+  Map1R +'&' +Map2R+'\n'+'真格('+GameModeS +'):'+Map1S+'&'+Map2S+'\n'+"组排("+GameModeL+"):"  +Map1L+'&' +Map2L



    return msg
