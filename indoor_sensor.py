#!/usr/bin/env python
# -*- coding: utf-8 -*-
import Adafruit_DHT


def room_temp(pin=20):
    h, t = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)
    if h is not None and t is not None:
        data = {"temp": str(round(t)), "humidity": str(round(h))}
        return data
    else:
        return {"temp": '0', "humidity": '0'}
