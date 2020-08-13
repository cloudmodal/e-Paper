#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import spidev
import RPi.GPIO
import logging

# Display resolution
EPD_WIDTH = 880
EPD_HEIGHT = 528
# Pin definition
RST_PIN = 17
DC_PIN = 25
CS_PIN = 8
BUSY_PIN = 24


class EPD:
    def __init__(self):
        self.reset_pin = RST_PIN
        self.dc_pin = DC_PIN
        self.busy_pin = BUSY_PIN
        self.cs_pin = CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.gp = RPi.GPIO
        # SPI device, bus = 0, device = 0
        self.SPI = spidev.SpiDev(0, 0)

    def digital_write(self, pin, value):
        self.gp.output(pin, value)

    def digital_read(self, pin):
        return self.gp.input(pin)

    @staticmethod
    def delay_ms(delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def module_init(self):
        self.gp.setmode(self.gp.BCM)
        self.gp.setwarnings(False)
        self.gp.setup(RST_PIN, self.gp.OUT)
        self.gp.setup(DC_PIN, self.gp.OUT)
        self.gp.setup(CS_PIN, self.gp.OUT)
        self.gp.setup(BUSY_PIN, self.gp.IN)
        self.SPI.max_speed_hz = 4000000
        self.SPI.mode = 0b00
        return 0

    def module_exit(self):
        logging.debug("spi end")
        self.SPI.close()
        logging.debug("close 5V, Module enters 0 power consumption ...")
        self.gp.output(RST_PIN, 0)
        self.gp.output(DC_PIN, 0)
        self.gp.cleanup()

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(4)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        logging.debug("e-Paper busy")
        busy = self.digital_read(self.busy_pin)

        while busy == 1:
            busy = self.digital_read(self.busy_pin)
        self.delay_ms(200)

    def init(self):
        if self.module_init() != 0:
            return -1

        self.reset()

        self.send_command(0x12)  # SWRESET
        self.ReadBusy()  # waiting for the electronic paper IC to release the idle signal

        self.send_command(0x46)  # Auto Write RAM
        self.send_data(0xF7)
        self.ReadBusy()  # waiting for the electronic paper IC to release the idle signal

        self.send_command(0x47)  # Auto Write RAM
        self.send_data(0xF7)
        self.ReadBusy()  # waiting for the electronic paper IC to release the idle signal

        self.send_command(0x0C)  # Soft start setting
        self.send_data(0xAE)
        self.send_data(0xC7)
        self.send_data(0xC3)
        self.send_data(0xC0)
        self.send_data(0x40)

        self.send_command(0x01)  # Set MUX as 527
        self.send_data(0xAF)
        self.send_data(0x02)
        self.send_data(0x01)

        self.send_command(0x11)  # Data entry mode
        self.send_data(0x01)

        self.send_command(0x44)
        self.send_data(0x00)  # RAM x address start at 0
        self.send_data(0x00)
        self.send_data(0x6F)  # RAM x address end at 36Fh -> 879
        self.send_data(0x03)
        self.send_command(0x45)
        self.send_data(0xAF)  # RAM y address start at 20Fh
        self.send_data(0x02)
        self.send_data(0x00)  # RAM y address end at 00h
        self.send_data(0x00)

        self.send_command(0x3C)  # VBD
        self.send_data(0x01)  # LUT1, for white

        self.send_command(0x18)
        self.send_data(0X80)
        self.send_command(0x22)
        self.send_data(0XB1)  # Load Temperature and waveform setting.
        self.send_command(0x20)
        self.ReadBusy()  # waiting for the electronic paper IC to release the idle signal

        self.send_command(0x4E)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_command(0x4F)
        self.send_data(0xAF)
        self.send_data(0x02)

        return 0

    def getbuffer(self, image):
        # logging.debug("bufsiz = ",int(self.width/8) * self.height)
        buf = [0xFF] * (int(self.width / 8) * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        logging.debug('imwidth = %d  imheight =  %d ', imwidth, imheight)
        if imwidth == self.width and imheight == self.height:
            logging.debug("Horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    if pixels[x, y] == 0:
                        buf[int((x + y * self.width) / 8)] &= ~(0x80 >> (x % 8))
        elif imwidth == self.height and imheight == self.width:
            logging.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        buf[int((newx + newy * self.width) / 8)] &= ~(0x80 >> (y % 8))
        return buf

    def display(self, imageblack, imagered):
        self.send_command(0x4F)
        self.send_data(0xAf)

        self.send_command(0x24)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(imageblack[i])

        self.send_command(0x26)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(~imagered[i])

        self.send_command(0x22)
        self.send_data(0xC7)  # Load LUT from MCU(0x32)
        self.send_command(0x20)
        self.delay_ms(200)  # !!!The delay here is necessary, 200uS at least!!!
        self.ReadBusy()

    def Clear(self):
        self.send_command(0x4F)
        self.send_data(0xAf)

        self.send_command(0x24)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xff)

        self.send_command(0x26)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0x00)

        self.send_command(0x22)
        self.send_data(0xC7)  # Load LUT from MCU(0x32)
        self.send_command(0x20)
        self.delay_ms(200)  # !!!The delay here is necessary, 200uS at least!!!
        self.ReadBusy()

    def sleep(self):
        self.send_command(0x10)  # deep sleep
        self.send_data(0x01)

        self.module_exit()
