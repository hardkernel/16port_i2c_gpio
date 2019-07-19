#!/usr/bin/python3

# Copyright 2012 Daniel Berlin (with some changes by Adafruit Industries/Limor Fried)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal  MCP230XX_GPIO(1, 0xin
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from i2c import I2C
import smbus
import time
import sys, getopt
from optparse import OptionParser

MCP23017_IODIRA = 0x00
MCP23017_IODIRB = 0x01
MCP23017_GPIOA  = 0x12
MCP23017_GPIOB  = 0x13
MCP23017_GPPUA  = 0x0C
MCP23017_GPPUB  = 0x0D
MCP23017_OLATA  = 0x14
MCP23017_OLATB  = 0x15

class MCP23017(object):
    OUTPUT = 0
    INPUT = 1

    def __init__(self, address, dev_node, busnum=-1):
        self.i2c = I2C(address=address, busnum=busnum,
                dev_node=dev_node)
        self.address = address

        self.i2c.write8(MCP23017_IODIRA, 0xFF)  # all inputs on port A
        self.i2c.write8(MCP23017_IODIRB, 0xFF)  # all inputs on port B
        self.direction = self.i2c.readU8(MCP23017_IODIRA)
        self.direction |= self.i2c.readU8(MCP23017_IODIRB) << 8
        self.i2c.write8(MCP23017_GPPUA, 0x00)
        self.i2c.write8(MCP23017_GPPUB, 0x00)

    def _changebit(self, bitmap, bit, value):
        assert value == 1 or value == 0, "Value is %s must be 1 or 0" % value
        if value == 0:
            return bitmap & ~(1 << bit)
        elif value == 1:
            return bitmap | (1 << bit)

    def _readandchangepin(self, port, pin, value, currvalue = None):
        assert pin >= 0 and pin < 16, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        #assert self.direction & (1 << pin) == 0, "Pin %s not set to output" % pin
        if not currvalue:
             currvalue = self.i2c.readU8(port)
        newvalue = self._changebit(currvalue, pin, value)
        self.i2c.write8(port, newvalue)
        return newvalue

    def pullup(self, pin, value):
        lvalue = self._readandchangepin(MCP23017_GPPUA, pin, value)
        if (pin < 8):
            return
        else:
            return self._readandchangepin(MCP23017_GPPUB, pin-8, value) << 8

    # Set pin to either input or output mode
    def config(self, pin, mode):
        if (pin < 8):
            self.direction = self._readandchangepin(MCP23017_IODIRA, pin, mode)
        else:
            self.direction |= self._readandchangepin(MCP23017_IODIRB, pin-8, mode) << 8

    def output(self, pin, value):
        # assert self.direction & (1 << pin) == 0, "Pin %s not set to output" % pin
        if (pin < 8):
            self.outputvalue = self._readandchangepin(MCP23017_GPIOA, pin, value, self.i2c.readU8(MCP23017_OLATA))
        else:
            self.outputvalue = self._readandchangepin(MCP23017_GPIOB, pin-8, value, self.i2c.readU8(MCP23017_OLATB)) << 8
        self.outputvalue = self._readandchangepin(MCP23017_IODIRA, pin, value, self.outputvalue)
        return self.outputvalue

    def input(self, pin):
        assert pin >= 0 and pin < self.num_gpios, "Pin number %s is invalid, only 0-%s are valid" % (pin, self.num_gpios)
        assert self.direction & (1 << pin) != 0, "Pin %s not set to input" % pin
        value = self.i2c.readU8(MCP23017_GPIOA)
        value |= self.i2c.readU8(MCP23017_GPIOB) << 8

        return value & (1 << pin)

def blink_led(mcp):
    [ mcp.config(i, mcp.OUTPUT) for i in range(16) ]
    print("CTRL+C to quit")
    while (True):
        [ mcp.output(i, 0) if (i+2)%2 else mcp.output(i, 1) for i in range(16) ]
        time.sleep(0.5);
        [ mcp.output(i, 1) if (i+2)%2 else mcp.output(i, 0) for i in range(16) ]
        time.sleep(0.5);

def main(argv):
    gpio = 0

    usage = " %prog I2CBUS blink"
    usage += "\n\t%prog I2CBUS -w GPIO [1|0]"
    usage += "\n\t%prog I2CBUS -r GPIO"

    parser = OptionParser(usage=usage)
    parser.add_option("-w", "--write", action='store_true', dest="w_gpio",
            help="Write HIGH or LOW to GPIO", metavar="GPIO")
    parser.add_option("-r", "--read", action='store_true', dest="r_gpio",
            help="Read from GPIO", metavar="GPIO")
    (options, args) = parser.parse_args()

    dev_node=int(args[0])

    if dev_node == 5 or dev_node == 6 or dev_node == 2 or dev_node == 3:
        i2c_bus = args[0]
        mcp = MCP23017(address = 0x20, dev_node=int(i2c_bus))
    else:
        parser.error('i2cbus has an invalid value.')

    if options.w_gpio and len(args) == 3:
        gpio = int(args[1])
        value = int(args[2])
        mcp.config(gpio, mcp.OUTPUT)
        mcp.output(gpio, value)
        print('write gpio{} value {}'.format(gpio, value))
    elif options.r_gpio and len(args) == 2:
        gpio = int(args[1])
        mcp.config(gpio, mcp.INPUT)
        value = mcp.input(gpio) >> gpio
        print('gpio{} value is {}'.format(gpio, value))
    elif 'blink' in args and len(args) == 2:
        blink_led(mcp)
    else:
        parser.print_help()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1:])
