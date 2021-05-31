#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import json
import yaml
import requests
import pylab as plt
import requests.utils
from skimage import io
from datetime import datetime
import matplotlib.font_manager as fm
from indoor_sensor import SHT30
from lib.location import Location
from weather_time_render import (
    weather, get_weather_fettle, get_prior_date, get_week_day
)
from lib import EPD, Logger
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'e-Paper.log')
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)

logger = Logger(LOG_FILE, level='debug').logger

# 获取传感器温度
sht30 = SHT30()

pic_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
lib_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')


if os.path.exists(lib_dir):
    sys.path.append(lib_dir)

now_date = datetime.now()


def login():
    """
    访问墨迹天气首页
    :return: 返回text格式
    """
    login_url = 'http://tianqi.moji.com/'
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit'
                      '/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safar'
                      'i/537.36',
    }

    try:
        rest = requests.get(url=login_url, headers=headers)
        return rest
    except Exception as err:
        print('无法建立新连接：\n{0}'.format(err))


def get_moji_cookies(rest):
    """
    获取站点cookies
    :param rest: 网站请求
    :return: cookies
    """
    cookies = rest.cookies
    cookie = requests.utils.dict_from_cookiejar(cookies)
    return cookie


def air_quality(air: int):
    if 0 <= air <= 50:
        return f'{air} 优'
    elif 51 <= air <= 100:
        return f'{air} 良'
    elif 101 <= air <= 150:
        return f'{air} 轻度污染'
    elif 151 <= air <= 200:
        return f'{air} 中度污染'
    elif 201 <= air <= 300:
        return f'{air} 重度污染'
    elif 301 <= air <= 500:
        return f'{air} 严重污染'
    else:
        return f'{air} 污染爆表'


def status_condition(Day, Night):
    if Day != Night:
        return f'{Day}转{Night}'
    else:
        return Day


def weather_data_render(draw1, draw2, celsius, **coordinate):
    """
    画图
    :param draw1:
    :param draw2:
    :param celsius:
    :param coordinate: 位置的坐标点
    :return:
    """
    place = coordinate['coordinate']
    # 天气图标
    icon = get_weather_fettle(place.get('f'))
    weather_icon = Image.open(os.path.join(pic_dir, icon))
    today_weather.paste(weather_icon, (place.get('weather_icon_left'), place.get('weather_icon_right')))
    # 当前气温显示
    draw1.text((place.get('temp_left'), place.get('temp_right')), place.get('t'), font=font24, fill=0)
    # 绘制温度的摄氏度图片
    celsius_image = Image.open(os.path.join(pic_dir, 'CELSIUS.BMP'))
    celsius.paste(celsius_image, (place.get('image_left'), place.get('image_right')))
    # 绘制天气状态
    draw1.text((place.get('condition_left'), place.get('condition_right')),  place.get('c'), font=font24, fill=0)
    # 绘制风力信息
    draw1.text((place.get('wind_left'), place.get('wind_right')),  place.get('w'), font=font24, fill=0)
    # 绘制湿度信息
    draw2.text((place.get('h_left'), place.get('h_right')),  place.get('h'), font=font24, fill=255)
    return draw1, draw2


def open_fletcher(f):
    try:
        with open(f, encoding='utf-8') as file:
            return yaml.safe_load(file)
    except TypeError:
        pass
    except FileNotFoundError:
        pass


def write_weather_data(forecasts: list):
    """
    获取15天的数据保存到文件
    :param forecasts:
    :return:
    """
    if len(forecasts) > 6:
        w_forecast_data = []
        for da in forecasts[1:6]:
            # 最低温度与最高温度
            temp = da['tempNight'] + '～' + da['tempDay']
            # 湿度 39%
            humidity = '湿度 ' + da['humidity'] + '%'
            # 天气状态
            if '07:00' >= now_date.strftime("%H:%M") <= '19:00':
                fettle = da['conditionDay']
                co = status_condition(da['conditionDay'], da['conditionNight'])
                wind = da['windDirDay'] + da['windLevelDay'] + '级'
            else:
                fettle = da['conditionNight']
                co = status_condition(da['conditionNight'], da['conditionDay'])
                wind = da['windDirNight'] + da['windLevelNight'] + '级'
            w_forecast_data.append({
                'temp': temp,
                'condition': co,
                'wind': wind,
                'humidity': humidity,
                'fettle': fettle
            })
        filename = "ForecastData.json"
        with open(filename, 'w') as f_obj:
            json.dump(w_forecast_data, f_obj, ensure_ascii=False)
        return w_forecast_data


def get_24hours_temp_data(get_data_url):
    """
    获取24小时气温数据
    :param get_data_url:
    :return:
    """
    log_in = login()
    cook = get_moji_cookies(log_in)
    rest = requests.get(url=get_data_url, cookies=cook)
    hour24 = rest.json()['hour24']
    hour = []
    temp = []
    humidity = []
    # 拿出我们需要的时间对应的温度
    for forecast in hour24[:18]:
        predict_hour = forecast['Fpredict_hour']
        if predict_hour == '0':
            hour.append('00:00')
        else:
            hour.append(str(predict_hour) + ':00')
        temp.append(forecast['Ftemp'])
        humidity.append(forecast['Fhumidity'])
    return forecast_24hours_temp(hours=hour, temps=temp)


def forecast_24hours_temp(hours, temps):
    file_name = 'FORECAST.png'
    # 设置图片大小
    plt.figure(figsize=(10.4, 1.8), dpi=100)
    # 设置字体,用来正常显示中文标签
    font = fm.FontProperties(fname=os.path.join(pic_dir, 'AdobeKaitiStd-Regular.otf'), size=12)
    plt.plot(hours, temps, label='未来24小时温度变化', color='r', linewidth=2.0, linestyle='--')
    plt.legend(prop=font)
    plt.savefig(os.path.join(pic_dir, file_name), transparent=True)
    # 转换格式
    new_file_name = "FORECAST" + ".BMP"
    im = Image.open(os.path.join(pic_dir, file_name))
    im.save(os.path.join(pic_dir, new_file_name))
    return new_file_name


def corp_margin(im):
    """
    为了减少图像信息的噪声或者视觉效果，需要去除图片周围的白色边框
    使用图片的RGB值判断是否属于边框，再确定物体的位置，对阈值的更改可以去除白色、黑色、或者任何纯色的边框
    :param im: 图片
    :return: 图片
    """
    img2 = im.sum(axis=2)
    (row, col) = img2.shape
    row_top = 0
    raw_down = 0
    col_top = 0
    col_down = 0
    for r in range(0, row):
        if img2.sum(axis=1)[r] < 700 * col:
            row_top = r
            break

    for r in range(row - 1, 0, -1):
        if img2.sum(axis=1)[r] < 700 * col:
            raw_down = r
            break

    for s in range(0, col):
        if img2.sum(axis=0)[s] < 760 * row:
            col_top = s
            break

    for x in range(col - 1, 0, -1):
        if img2.sum(axis=0)[x] < 700 * row:
            col_down = x
            break

    new_img = im[row_top:raw_down + 1, col_top:col_down + 1, 0:3]
    return new_img


def weather_trend_draw():
    fine = get_24hours_temp_data('http://tianqi.moji.com/index/getHour24')
    # 读取图片
    img = io.imread(os.path.join(pic_dir, fine))
    # 图片修改
    img_re = corp_margin(img)
    # 保存图片
    io.imsave(os.path.join(pic_dir, fine), img_re)
    images = Image.open(os.path.join(pic_dir, fine))
    today_date.paste(images, (20, 365))


def fetcher_errors(images, drafts, msg="咦？设备好像出错了呀！"):
    img = Image.open(os.path.join(pic_dir, 'ERROR.bmp'))
    images.paste(img, (60, 20))
    drafts.text((100, 160), msg, font=font48, fill=0)
    return drafts


try:
    # 读取天气位置坐标配置
    weather_coordinate = open_fletcher(os.path.join(BASE_DIR, 'weather_coordinate_fletcher.yml'))
    logger.info('加载位置信息...')
    location = Location()
    Latitude = location.Location_Latitude()
    Longitude = location.Location_Longitude()
    logger.info('位置信息加载成功，正在获取天气信息...')
    # 获取天气实况
    weather_fletcher = weather(Latitude, Longitude, 'condition')
    # 获取7天预报
    forecast_days = weather(Latitude, Longitude, 'forecast15days')
    forecast_data = write_weather_data(forecast_days.get('forecast'))
    # 获取空气质量
    aqi = weather(Latitude, Longitude, 'aqi')['aqi']
    condition = weather_fletcher.get('condition')

    epd = EPD()
    logger.info("墨水屏正在初始化")
    epd.init()
    logger.info('清理屏幕旧信息')
    epd.Clear()
    logger.info('屏幕信息清理完成')

    # 字体大小
    font24 = ImageFont.truetype(os.path.join(pic_dir, 'AdobeKaitiStd-Regular.otf'), 24)
    font18 = ImageFont.truetype(os.path.join(pic_dir, 'AdobeKaitiStd-Regular.otf'), 18)
    font72 = ImageFont.truetype(os.path.join(pic_dir, 'AdobeKaitiStd-Regular.otf'), 72)
    font48 = ImageFont.truetype(os.path.join(pic_dir, 'AdobeKaitiStd-Regular.otf'), 48)

    # Drawing on the Horizontal image
    logger.info("Drawing on the Horizontal image...")
    """
    定义一个图像缓存，以方便在图片上进行画图、写字等功能
    第一个参数定义图片的颜色深度，定义为1说明是2位图
    第二个参数是一个元组，定义好图片的宽度和高度
    第三个参数是定义缓存的默认颜色，0为黑色，255为白色
    """
    today_date = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    today_weather = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame

    # 创建一个基于image的画图对象，所有的画图操作都在这个对象上
    draw_date = ImageDraw.Draw(today_date)
    draw_weather = ImageDraw.Draw(today_weather)
    logger.info('创建一个基于image的画图对象')
    # 获取未来五天的日期
    m = now_date.month
    d = now_date.day
    w = get_week_day(now_date)

    draw_date.text((10, 2), f'今天是：{m}月{d}日 {w} ({now_date.strftime("%H:%M")}更新)', font=font24, fill=0)
    # 获取今日天气提示
    logger.info('获取今日天气提示')
    draw_date.text((430, 1), condition.get('tips'), font=font24, fill=0)
    draw_date.text((260, 50), f'{get_prior_date(1).month}月{get_prior_date(1).day}日', font=font24, fill=0)
    draw_date.text((270, 80), f'{get_week_day(get_prior_date(1))}', font=font24, fill=0)
    draw_date.text((420, 50), f'{get_prior_date(2).month}月{get_prior_date(2).day}日', font=font24, fill=0)
    draw_date.text((430, 80), f'{get_week_day(get_prior_date(2))}', font=font24, fill=0)
    draw_date.text((580, 50), f'{get_prior_date(3).month}月{get_prior_date(3).day}日', font=font24, fill=0)
    draw_date.text((590, 80), f'{get_week_day(get_prior_date(3))}', font=font24, fill=0)
    draw_date.text((740, 50), f'{get_prior_date(4).month}月{get_prior_date(4).day}日', font=font24, fill=0)
    draw_date.text((750, 80), f'{get_week_day(get_prior_date(4))}', font=font24, fill=0)
    # 绘制一条红色区域
    draw_weather.rectangle((40, 330, 850, 360), outline=0, fill=0)
    logger.info('绘制一条红色区域')
    # 气温数据
    for idx, item in enumerate(weather_coordinate):
        if idx == 0:
            # 获取当前气温,显示天气状态图标
            now_fettle = condition.get('condition')
        else:
            now_fettle = forecast_data[idx]['fettle']
        item.update(
            {
                'f': now_fettle,
                't': forecast_data[idx]['temp'],
                'c': forecast_data[idx]['condition'],
                'w': forecast_data[idx]['wind'],
                'h': forecast_data[idx]['humidity']
            }
        )
        weather_data_render(
            draw_date, draw_weather, today_date,
            coordinate=item
        )
    logger.info('获取天气信息成功！')
    draw_weather.text((30, 130), '室', font=font24, fill=0)
    draw_weather.text((30, 170), '外', font=font24, fill=0)
    celsius1 = Image.open(os.path.join(pic_dir, 'CELSIUS.BMP'))

    aqq = air_quality(int(aqi['value']))
    if len(condition.get('temp')) == 1:
        draw_weather.text((60, 120), condition.get('temp'), font=font72, fill=0)
        today_weather.paste(celsius1, (105, 130))
        draw_weather.text((105, 160), aqq, font=font24, fill=0)
    elif len(condition.get('temp')) == 2:
        draw_weather.text((60, 120), condition.get('temp'), font=font72, fill=0)
        today_weather.paste(celsius1, (150, 130))
        draw_weather.text((150, 160), aqq, font=font24, fill=0)
    else:
        draw_weather.text((60, 140), condition.get('temp'), font=font72, fill=0)
        today_weather.paste(celsius1, (180, 130))
        draw_weather.text((180, 200), aqq, font=font24, fill=0)

    # 显示室内温度
    sht30.write_command()
    result = sht30.read_data()
    h = " %.1f" % (result['h'])
    c = " %.1f" % (result['c'])
    heat_img = Image.open(os.path.join(pic_dir, 'HEAT.bmp'))
    today_weather.paste(heat_img, (30, 200))
    draw_weather.text((60, 200), c + '℃', font=font24, fill=0)
    # 显示室内湿度
    humidity_img = Image.open(os.path.join(pic_dir, 'HUMIDITY.bmp'))
    today_date.paste(humidity_img, (150, 200))
    draw_date.text((180, 200), h + '%', font=font24, fill=0)

    logger.info("获取未来24小时气温")
    # 获取24小时气温数据
    weather_trend_draw()
    epd.display(epd.getbuffer(today_date), epd.getbuffer(today_weather))

except IndexError as e:
    epd = EPD()
    image = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)
    fetcher_errors(image, draw)
    epd.display(epd.getbuffer(image), epd.getbuffer(image))
    logger.error(e)

except TypeError as e:
    epd = EPD()
    image = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)
    fetcher_errors(image, draw)
    epd.display(epd.getbuffer(image), epd.getbuffer(image))
    logger.error(e)

except FileNotFoundError as e:
    epd = EPD()
    image = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)
    fetcher_errors(image, draw)
    epd.display(epd.getbuffer(image), epd.getbuffer(image))
    logger.error(e)

except IOError as e:
    epd = EPD()
    image = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)
    fetcher_errors(image, draw)
    epd.display(epd.getbuffer(image), epd.getbuffer(image))
    logger.error(e)

except KeyboardInterrupt:
    epd = EPD()
    logger.info("ctrl + c:")
    epd.module_exit()
    exit()
