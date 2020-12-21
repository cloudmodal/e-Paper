#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import smbus
import Adafruit_DHT

# Get I2C bus
bus = smbus.SMBus(1)

# I2C address of the device
SHT30_DEFAULT_ADDRESS = 0x44

# SHT30 Command Set
SHT30_MEAS_REP_STRETCH_EN = 0x2C  # Clock stretching enabled
SHT30_MEAS_HIGH_REP_STRETCH_EN = 0x06  # High repeatability measurement with clock stretching enabled
SHT30_MEAS_MED_REP_STRETCH_EN = 0x0D  # Medium repeatability measurement with clock stretching enabled
SHT30_MEAS_LOW_REP_STRETCH_EN = 0x10  # Low repeatability measurement with clock stretching enabled
SHT30_MEAS_REP_STRETCH_DS = 0x24  # Clock stretching disabled
SHT30_MEAS_HIGH_REP_STRETCH_DS = 0x00  # High repeatability measurement with clock stretching disabled
SHT30_MEAS_MED_REP_STRETCH_DS = 0x0B  # Medium repeatability measurement with clock stretching disabled
SHT30_MEAS_LOW_REP_STRETCH_DS = 0x16  # Low repeatability measurement with clock stretching disabled
SHT30_CMD_READSTATUS = 0xF32D  # Command to read out the status register
SHT30_CMD_CLEARSTATUS = 0x3041  # Command to clear the status register
SHT30_CMD_SOFTRESET = 0x30A2  # Soft reset command
SHT30_CMD_HEATERENABLE = 0x306D  # Heater enable command
SHT30_CMD_HEATERDISABLE = 0x3066  # Heater disable command


class SHT30:
    def __init__(self):
        self.write_command()
        time.sleep(0.3)
        self.read_data()

    @staticmethod
    def write_command():
        """Select the temperature & humidity command from the given provided values"""
        COMMAND = [SHT30_MEAS_HIGH_REP_STRETCH_EN]
        bus.write_i2c_block_data(SHT30_DEFAULT_ADDRESS, SHT30_MEAS_REP_STRETCH_EN, COMMAND)

    @staticmethod
    def read_data():
        """Read data back from device address, 6 bytes
        temp MSB, temp LSB, temp CRC, humidity MSB, humidity LSB, humidity CRC"""
        data = bus.read_i2c_block_data(SHT30_DEFAULT_ADDRESS, 6)

        # Convert the data
        temp = data[0] * 256 + data[1]
        cTemp = -45 + (175 * temp / 65535.0)
        fTemp = -49 + (315 * temp / 65535.0)
        humidity = 100 * (data[3] * 256 + data[4]) / 65535.0

        return {'c': cTemp, 'f': fTemp, 'h': humidity}


def room_temp(pin=20):
    h, t = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)
    if h is not None and t is not None:
        data = {"c": str(round(t)), "h": str(round(h))}
        return data
    else:
        return {"c": '0', "h": '0'}
