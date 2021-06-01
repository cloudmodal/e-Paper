#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import requests
from datetime import datetime, timedelta


logging.basicConfig(level=logging.DEBUG)

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
        u'雷阵雨': 'WLZYU.BMP', u'小雨': 'WQING1.BMP', u'中雨': 'WQING1.BMP', u'大雨': 'WQING1.BMP',
        u'雪': 'WXUE.BMP', u'雹': 'WBBAO.BMP'
    }.get(cw, None)

    if not bmp_name:
        if u'雾' in cw or u'霾' in cw:
            bmp_name = 'WWU.BMP'

    return bmp_name


def weather(latitude, longitude, forecast):
    """
    调用墨迹天气API接口
    :param latitude: 纬度
    :param longitude: 经度
    :param forecast: 预测时间范围
    :return: JSON字符串
    """
    url = f'http://aliv8.data.moji.com/whapi/json/aliweather/{forecast}'

    Header = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "Authorization": "APPCODE 2c1c7b1e6ff74ae494c3a6b48036af77"
        }
    body = {
        'lat': latitude,
        'lon': longitude,
    }
    rest = requests.post(url, data=body, headers=Header)
    if rest.status_code == 200 and rest.json()['code'] == 0:
        data = rest.json()['data']
        return data
    else:
        print(rest)
