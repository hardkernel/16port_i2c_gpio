import smbus

class I2C(object):
    def __init__(self, address, busnum=-1, dev_node=5):
        self.address = address
        self.bus = smbus.SMBus(dev_node);

    def write8(self, reg, value):
        "Writes an 8-bit value to the specified register/address"
        try:
            self.bus.write_byte_data(self.address, reg, value)
        except IOError:
            return print('IOError')

    def readU8(self, reg):
        "Read an unsigned byte from the I2C device"
        try:
            result = self.bus.read_byte_data(self.address, reg)
            return result
        except IOError:
            return print('IOError')

if __name__ == '__main__':
    try:
        bus = I2C(address=0x28)
        print("Default I2C bus is accessible")
    except:
        print("Error accessing default I2C bus")
