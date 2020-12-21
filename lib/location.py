#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import ssl
import yaml
from urllib.request import urlopen
from json import load
import geoip2.database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ssl._create_default_https_context = ssl._create_unverified_context


reader = geoip2.database.Reader(os.path.join(BASE_DIR, 'GeoLite2-City.mmdb'))


def get_ip():
    ip = load(urlopen('https://api.ipify.org/?format=json'))['ip']
    return ip


def get_config_key(config):
    try:
        with open(config, encoding='utf-8') as f:
            return yaml.safe_load(f)
    except TypeError:
        pass
    except FileNotFoundError:
        pass


class Location:
    def __init__(self):
        self.ip = get_ip()
        self.seven_days = None
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
