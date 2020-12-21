#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: sun
@license: (C) Copyright 2016-2019, Light2Cloud (Beijing) Web Service Co., LTD
@contact: wenhaijie@light2cloud.com
@software: L2CloudCMP
@file: utils.py
@ide: PyCharm
@time: 2020/12/21 16:00
@desc:
"""
import logging
from logging import handlers


class Logger(object):
    level_relations = {
        'debug': logging.DEBUG,  # 详细信息，一般只在调试问题时使用。
        'info': logging.INFO,  # 证明事情按预期工作。
        'warning': logging.WARNING,  # 某些没有预料到的事件的提示，或可能会出现的问题提示。例如：磁盘空间不足。但是软件还是会照常运行。
        'error': logging.ERROR,  # 由于更严重的问题，软件已不能执行一些功能了。
        'crit': logging.CRITICAL  # 严重错误，表明软件已不能继续运行了。
    }

    def __init__(
            self,
            filename,
            level='info',
            when='D',
            backCount=3,
            fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
    ):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt)  # 设置日志格式
        self.logger.setLevel(self.level_relations.get(level))  # 设置日志级别
        sh = logging.StreamHandler()  # 往屏幕上输出
        sh.setFormatter(format_str)  # 设置屏幕上显示的格式
        # 往文件里写入# 指定间隔时间自动生成文件的处理器
        th = handlers.TimedRotatingFileHandler(
            filename=filename, when=when, backupCount=backCount, encoding='utf-8'
        )
        # 实例化TimedRotatingFileHandler
        # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
        # S 秒
        # M 分
        # H 小时、
        # D 天、
        # W 每星期（interval==0时代表星期一）
        # midnight 每天凌晨
        th.setFormatter(format_str)  # 设置文件里写入的格式
        self.logger.addHandler(sh)  # 把对象加到logger里
        self.logger.addHandler(th)
