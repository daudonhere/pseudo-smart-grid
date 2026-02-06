from machine import Pin, SPI
import framebuf

class NokiaLCD:
    WIDTH = 84
    HEIGHT = 48
    def __init__(self, spi, dc, cs, rst):
        self.spi = spi
        self.dc = dc
        self.cs = cs
        self.rst = rst
        self.dc.init(Pin.OUT, value=0)
        self.cs.init(Pin.OUT, value=1)
        self.rst.init(Pin.OUT, value=1)
        self.buffer = bytearray(self.WIDTH * self.HEIGHT // 8)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.WIDTH, self.HEIGHT, framebuf.MONO_VLSB)
        self.reset()
        self.init_lcd()
    def contrast(self, value):
        if value < 0:
            value = 0
        elif value > 127:
            value = 127
        self.write_cmd(0x21)
        self.write_cmd(0x80 | value)
        self.write_cmd(0x20)

    def reset(self):
        self.rst.value(0)
        self.rst.value(1)

    def init_lcd(self):
        self.write_cmd(0x21)
        self.write_cmd(0xB0)
        self.write_cmd(0x04)
        self.write_cmd(0x14)
        self.write_cmd(0x20)
        self.write_cmd(0x0C)

    def write_cmd(self, cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytearray([data]))
        self.cs.value(1)

    def clear(self):
        for i in range(len(self.buffer)):
            self.buffer[i] = 0

    def text(self, string, x, y):
        self.framebuf.text(string, x, y, 1)

    def show(self):
        for i in range(6):
            self.write_cmd(0x40 | i)
            self.write_cmd(0x80)
            for j in range(84):
                self.write_data(self.buffer[i*84 + j])
