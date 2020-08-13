#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ssl
import gzip
from urllib.request import urlopen
from json import load
from io import BytesIO
import geoip2.database


ssl._create_default_https_context = ssl._create_unverified_context


reader = geoip2.database.Reader('GeoLite2-City.mmdb')


def get_ip():
    ip = load(urlopen('https://api.ipify.org/?format=json'))['ip']
    return ip


class Location:
    def __init__(self):
        self.ip = get_ip()
        self.response = reader.city(self.ip)

    def Country_IsoCode(self):
        """
        :return: 返回国家代码
        """
        return self.response.country.iso_code

    def Country_NameCN(self):
        """

        :return: 返回国家名称(中文显示)
        """
        return self.response.country.names['zh-CN']

    def country_name(self):
        """
        :return: 返回国家名称
        """
        return self.response.country.name

    def country_specific_name(self):
        """
        :return: 返回州(国外)/省(国内)名称
        """
        return self.response.subdivisions.most_specific.name

    def Country_SpecificIsoCode(self):
        """

        :return: 返回州(国外)/省(国内)代码
        """
        return self.response.subdivisions.most_specific.iso_code

    def City_Name(self):
        """

        :return: 返回城市名称
        """
        return self.response.city.name

    def City_PostalCode(self):
        """

        :return: 返回邮政编码
        """
        return self.response.postal.code

    def Location_Latitude(self):
        """

        :return: 返回纬度
        """
        return self.response.location.latitude

    def Location_Longitude(self):
        """

        :return: 返回经度
        """
        return self.response.location.longitude

    @staticmethod
    def city_search(key, location, adm=''):
        """
        可获取到需要查询城市的基本信息，包括城市或地区的Location ID（你需要这个ID去查询天气）
        :param key: 用户认证key，例如 key=123456789ABC
        :param location: 输入需要查询的城市名称，例如location=beijing
        :param adm: 城市所属行政区划，例如adm=beijing
        :return: 返回查询结果为Json格式数据
        """
        url = 'https://geoapi.heweather.net/v2/city/lookup?'
        city = urlopen(url + f'key={key}&location={location}&adm={adm}').read()
        buff = BytesIO(city)
        f = gzip.GzipFile(fileobj=buff)
        html = f.read().decode('utf-8')
        return html
