#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys
import time
import json
import logging
import requests
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from lib import EPD
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

pic_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
lib_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')


if os.path.exists(lib_dir):
    sys.path.append(lib_dir)

logging.basicConfig(level=logging.DEBUG)

# 城市ID
city = 2
now_date = datetime.now()


def get_prior_date(days):
    date = now_date + timedelta(days=days)
    return date


def get_week_day(date):
    week_day_dict = {
        0: '星期一',
        1: '星期二',
        2: '星期三',
        3: '星期四',
        4: '星期五',
        5: '星期六',
        6: '星期日',
    }
    day = date.weekday()
    return week_day_dict[day]


def get_weather_fettle(cw):
    bmp_name = {
        u'晴': 'WQING.BMP', u'阴': 'WYIN.BMP', u'多云': 'WDYZQ.BMP', u'雨': 'WYU.BMP',
        u'雷阵雨': 'WLZYU.BMP', u'小雨': 'WXYU.BMP', u'中雨': 'WXYU.BMP', u'大雨': 'WXYU.BMP',
        u'雪': 'WXUE.BMP', u'雹': 'WBBAO.BMP'
    }.get(cw, None)

    if not bmp_name:
        if u'雾' in cw or u'霾' in cw:
            bmp_name = 'WWU.BMP'

    return bmp_name


def weatherReal(cityId, forecast='forecast15days'):
    """
    通过墨迹天气API，获取未来15天的数据
    :param forecast:
    :param cityId: 城市ID
    :return: 15天的天气数据forecast24hours
    """
    url = f'http://aliv18.data.moji.com/whapi/json/alicityweather/{forecast}'

    Header = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "Authorization": "APPCODE 2c1c7b1e6ff74ae494c3a6b48036af77"
        }

    body = {
        'cityId': cityId,
    }
    rest = requests.post(url, data=body, headers=Header)
    if rest.status_code == 200:
        rest = json.loads(rest.text)
    return rest


def future_weather(date):
    try:
        with open('forecast15days.json') as f_obj:
            forecast = json.load(f_obj)
        for fore in forecast:
            if fore.get('predictDate') == date:
                return fore['data']
    except PermissionError as pe:
        logging.error(pe)
    except FileNotFoundError as es:
        logging.error(es)


def get_15d_weather(forecast: dict):
    """
    获取15天的数据保存到文件
    :param forecast:
    :return:
    """
    if 'data' in forecast:
        data = forecast.get('data')
        try:
            re = data.get('forecast')
            new_data = []
            for fore in range(1, len(re)):
                n = re[fore]
                new_data.append(
                    {
                        'predictDate': n.get('predictDate'),
                        'data': n
                    }
                )
            filename = "forecast15days.json"
            with open(filename, 'w') as f_obj:
                json.dump(new_data, f_obj, ensure_ascii=False)
        except KeyError:
            logging.debug('Parameter error')


def get_datetime(day):
    da = datetime.now() + timedelta(days=day)
    return da


def forecast_24hours(weather):
    hour = []
    temp = []
    for tem in weather:
        te = int(tem['temp'])
        ho = tem['hour']
        if ho == '0':
            hour.append('00:00')
        else:
            hour.append(ho + ':00')
        temp.append(te)

    file_name = 'FORECAST.png'
    # 设置图片大小
    plt.figure(figsize=(9, 1.8), dpi=100)
    # 用来正常显示中文标签
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.plot(hour, temp, label='Ten hours temperature change', color='b', linewidth=3, linestyle='-.')
    plt.legend()
    plt.savefig(os.path.join(pic_dir, file_name), transparent=True)
    # 等待两秒
    time.sleep(2)
    # 转换格式
    new_file_name = "FORECAST" + ".BMP"
    im = Image.open(os.path.join(pic_dir, file_name))
    im.save(os.path.join(pic_dir, new_file_name))
    return new_file_name


try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit'
                      '/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safar'
                      'i/537.36',
    }
    # 下载墨迹天气主页源码
    res = requests.get('http://tianqi.moji.com/', headers=headers)
    # 用BeautifulSoup获取所需信息
    soup = BeautifulSoup(res.text, "html.parser")
    # 当前温度
    now_temp = soup.find('div', attrs={'class': 'wea_weather clearfix'}).em.getText()
    # 当前天气状态
    now_fettle = soup.find('div', attrs={'class': 'wea_weather clearfix'}).b.getText()
    # 获取今日天气提示
    wea_tips = soup.find('div', attrs={'class': 'wea_tips clearfix'}).em.getText()
    # 获取风向
    now_wea_about = soup.find('div', attrs={'class': 'wea_about clearfix'}).em.getText()
    # 获取空气质量
    now_level = soup.find('div', attrs={'class', 'wea_alert clearfix'}).em.getText()
    # 获取湿度
    humidity = soup.find('div', attrs={'class': 'wea_about clearfix'}).span.get_text()
    # 获取最高与最低温度
    wp_item = soup.find('li', attrs={'class': 'item active'}).p.get_text()
    wp = wp_item.replace('°', '').split('/')

    logging.info("获取未来天气")
    dt = weatherReal(city)
    get_15d_weather(dt)

    epd = EPD()
    logging.info("init and Clear")
    epd.init()
    epd.Clear()

    # 字体大小
    font24 = ImageFont.truetype(os.path.join(pic_dir, 'Font.ttc'), 24)
    font18 = ImageFont.truetype(os.path.join(pic_dir, 'Font.ttc'), 18)
    font72 = ImageFont.truetype(os.path.join(pic_dir, 'Font.ttc'), 72)
    font48 = ImageFont.truetype(os.path.join(pic_dir, 'Font.ttc'), 48)

    # Drawing on the Horizontal image
    logging.info("Drawing on the Horizontal image...")
    today_date = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    today_weather = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame

    draw_date = ImageDraw.Draw(today_date)
    draw_weather = ImageDraw.Draw(today_weather)

    # 获取未来五天的日期
    m = now_date.month
    d = now_date.day
    w = get_week_day(now_date)

    draw_date.text((10, 1), f'今天是：{m}月{d}日 {w} ({now_date.strftime("%H:%M")}更新)', font=font24, fill=0)
    # 每日一句话
    draw_date.text((400, 1), wea_tips, font=font24, fill=0)
    draw_date.text((260, 50), f'{get_prior_date(1).month}月{get_prior_date(1).day}日', font=font24, fill=0)
    draw_date.text((260, 80), f'{get_week_day(get_prior_date(1))}', font=font24, fill=0)
    draw_date.text((420, 50), f'{get_prior_date(2).month}月{get_prior_date(2).day}日', font=font24, fill=0)
    draw_date.text((420, 80), f'{get_week_day(get_prior_date(2))}', font=font24, fill=0)
    draw_date.text((580, 50), f'{get_prior_date(3).month}月{get_prior_date(3).day}日', font=font24, fill=0)
    draw_date.text((580, 80), f'{get_week_day(get_prior_date(3))}', font=font24, fill=0)
    draw_date.text((740, 50), f'{get_prior_date(4).month}月{get_prior_date(4).day}日', font=font24, fill=0)
    draw_date.text((740, 80), f'{get_week_day(get_prior_date(4))}', font=font24, fill=0)

    # 获取当前气温,显示天气状态图标
    bmp = Image.open(os.path.join(pic_dir, get_weather_fettle(now_fettle)))
    today_weather.paste(bmp, (50, 30))
    # 显示未来四天天气状态图标

    # 获取本地的数据
    datetime2 = get_datetime(1)
    future2 = future_weather(datetime2.strftime("%Y-%m-%d"))
    now_time = datetime2.strftime("%Y-%m-%d %H:%M:%S")
    if future2['sunrise'] < now_time < future2['sunset']:
        condition2 = future2['conditionDay']
    else:
        condition2 = future2['conditionNight']
    celsius2 = Image.open(os.path.join(pic_dir, get_weather_fettle(condition2)))
    today_weather.paste(celsius2, (230, 110))

    datetime3 = get_datetime(2)
    future3 = future_weather(datetime3.strftime("%Y-%m-%d"))
    now_time = datetime3.strftime("%Y-%m-%d %H:%M:%S")
    if future3['sunrise'] < now_time < future3['sunset']:
        condition3 = future3['conditionDay']
    else:
        condition3 = future3['conditionNight']
    celsius3 = Image.open(os.path.join(pic_dir, get_weather_fettle(condition3)))
    today_weather.paste(celsius3, (390, 110))

    datetime4 = get_datetime(3)
    future4 = future_weather(datetime4.strftime("%Y-%m-%d"))
    now_time = datetime4.strftime("%Y-%m-%d %H:%M:%S")
    if future4['sunrise'] < now_time < future4['sunset']:
        condition4 = future4['conditionDay']
    else:
        condition4 = future4['conditionNight']
    celsius4 = Image.open(os.path.join(pic_dir, get_weather_fettle(condition4)))
    today_weather.paste(celsius4, (550, 110))

    datetime5 = get_datetime(4)
    future5 = future_weather(datetime5.strftime("%Y-%m-%d"))
    now_time = datetime5.strftime("%Y-%m-%d %H:%M:%S")
    if future5['sunrise'] < now_time < future5['sunset']:
        condition5 = future5['conditionDay']
    else:
        condition5 = future5['conditionNight']
    celsius5 = Image.open(os.path.join(pic_dir, get_weather_fettle(condition5)))
    today_weather.paste(celsius5, (710, 110))

    # 显示温度
    draw_weather.text((30, 150), now_temp, font=font72, fill=0)
    celsius1 = Image.open(os.path.join(pic_dir, 'CELSIUS.BMP'))
    today_weather.paste(celsius1, (110, 165))
    draw_weather.text((110, 190), now_fettle, font=font24, fill=0)

    # 当前气温显示
    draw_date.text((50, 240), f'{wp[0]}～{wp[1]}', font=font24, fill=0)
    celsius2 = Image.open(os.path.join(pic_dir, 'CELSIUS.BMP'))
    today_date.paste(celsius2, (130, 243))
    draw_date.text((40, 270), humidity, font=font24, fill=0)
    draw_date.text((40, 300), now_wea_about, font=font24, fill=0)
    draw_weather.rectangle((40, 330, 850, 360), outline=0, fill=0)
    draw_weather.text((45, 330), now_level, font=font24, fill=255)

    # 第二天天气
    tempNight2 = future_weather(datetime2.strftime("%Y-%m-%d"))['tempNight']
    tempDay2 = future_weather(datetime2.strftime("%Y-%m-%d"))['tempDay']
    draw_date.text((250, 240), f'{tempNight2}～{tempDay2}', font=font24, fill=0)
    celsius2 = Image.open(os.path.join(pic_dir, 'CELSIUS.BMP'))
    today_date.paste(celsius2, (330, 243))
    # '晴转雷阵雨'
    if future2['conditionDay'] == future2['conditionNight']:
        draw_date.text((250, 270), future2['conditionDay'], font=font24, fill=0)
    else:
        draw_date.text((250, 270), future2['conditionDay'] + "转" + future2['conditionNight'], font=font24, fill=0)
    # 获取风向
    if future2['sunrise'] < now_time < future2['sunset']:
        win2 = future2['windDirDay']
        win_leve2 = future2['windLevelDay']
    else:
        win2 = future2['windDirNight']
        win_leve2 = future2['windLevelNight']
    draw_date.text((250, 300), f'{win2}{win_leve2}级', font=font24, fill=0)  # '东南风2级'
    # draw_weather.rectangle((850, 330, 180, 360), outline=0, fill=0)
    draw_weather.text((255, 330), '湿度' + future2['humidity'] + '%', font=font24, fill=255)

    # 第三天天气
    tempNight3 = future_weather(datetime3.strftime("%Y-%m-%d"))['tempNight']
    tempDay3 = future_weather(datetime3.strftime("%Y-%m-%d"))['tempDay']
    draw_date.text((410, 240), f'{tempNight3}～{tempDay3}', font=font24, fill=0)
    celsius2 = Image.open(os.path.join(pic_dir, 'CELSIUS.BMP'))
    today_date.paste(celsius2, (490, 243))
    # '晴转雷阵雨'
    if future3['conditionDay'] == future3['conditionNight']:
        draw_date.text((410, 270), future3['conditionDay'], font=font24, fill=0)
    else:
        draw_date.text((410, 270), future3['conditionDay'] + "转" + future3['conditionNight'], font=font24, fill=0)
    # 获取风向
    if future3['sunrise'] < now_time < future3['sunset']:
        win3 = future3['windDirDay']
        win_leve3 = future3['windLevelDay']
    else:
        win3 = future3['windDirNight']
        win_leve3 = future3['windLevelNight']
    draw_date.text((410, 300), f'{win3}{win_leve3}级', font=font24, fill=0)
    draw_weather.text((410, 330), '湿度' + future3['humidity'] + '%', font=font24, fill=255)

    # 第四天天气
    tempNight4 = future_weather(datetime4.strftime("%Y-%m-%d"))['tempNight']
    tempDay4 = future_weather(datetime4.strftime("%Y-%m-%d"))['tempDay']
    draw_date.text((570, 240), f'{tempNight4}～{tempDay4}', font=font24, fill=0)
    celsius2 = Image.open(os.path.join(pic_dir, 'CELSIUS.BMP'))
    today_date.paste(celsius2, (650, 243))
    # '晴转雷阵雨'
    if future4['conditionDay'] == future4['conditionNight']:
        draw_date.text((570, 270), future4['conditionDay'], font=font24, fill=0)
    else:
        draw_date.text((570, 270), future4['conditionDay'] + "转" + future4['conditionNight'], font=font24, fill=0)
    # 获取风向
    if future4['sunrise'] < now_time < future4['sunset']:
        win4 = future4['windDirDay']
        win_leve4 = future4['windLevelDay']
    else:
        win4 = future4['windDirNight']
        win_leve4 = future4['windLevelNight']
    draw_date.text((570, 300), f'{win4}{win_leve4}级', font=font24, fill=0)
    draw_weather.text((570, 330), '湿度' + future4['humidity'] + '%', font=font24, fill=255)

    # 第五天天气
    tempNight5 = future_weather(datetime5.strftime("%Y-%m-%d"))['tempNight']
    tempDay5 = future_weather(datetime5.strftime("%Y-%m-%d"))['tempDay']
    draw_date.text((730, 240), f'{tempNight5}～{tempDay5}', font=font24, fill=0)
    celsius2 = Image.open(os.path.join(pic_dir, 'CELSIUS.BMP'))
    today_date.paste(celsius2, (810, 243))
    # '晴转雷阵雨'
    if future5['conditionDay'] == future5['conditionNight']:
        draw_date.text((730, 270), future5['conditionDay'], font=font24, fill=0)
    else:
        draw_date.text((730, 270), future5['conditionDay'] + "转" + future5['conditionNight'], font=font24, fill=0)
    # 获取风向
    if future5['sunrise'] < now_time < future5['sunset']:
        win5 = future5['windDirDay']
        win_leve5 = future5['windLevelDay']
    else:
        win5 = future5['windDirNight']
        win_leve5 = future5['windLevelNight']
    draw_date.text((730, 300), f'{win5}{win_leve5}级', font=font24, fill=0)
    draw_weather.text((730, 330), '湿度' + future5['humidity'] + '%', font=font24, fill=255)

    # 24小时预报
    try:
        # 获取最近十个小时的数据
        we = weatherReal(city, forecast='forecast24hours')
        fine = forecast_24hours(we['data']['hourly'][0:10])
        celsius24 = Image.open(os.path.join(pic_dir, fine))
        today_date.paste(celsius24, (1, 345))
    except FileNotFoundError:
        celsius24 = Image.open(os.path.join(pic_dir, 'SCALE.BMP'))
        today_date.paste(celsius24, (60, 369))
        draw_date.text((239, 420), "咦？数据丢失了！", font=font48, fill=0)
    epd.display(epd.getbuffer(today_date), epd.getbuffer(today_weather))

    # logging.info("Clear...")
    # epd.init()
    # epd.Clear()

    # logging.info("Goto Sleep...")
    # epd.sleep()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    epd = EPD()
    logging.info("ctrl + c:")
    epd.module_exit()
    exit()
