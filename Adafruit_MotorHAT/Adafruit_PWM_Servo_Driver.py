import time
import math
import logging

import Adafruit_GPIO.I2C as I2C

from .Adafruit_Revision import get_pi_revision

# ============================================================================
# Adafruit PCA9685 16-Channel PWM Servo Driver
# ============================================================================

def get_pi_ic2_bus():
    # Gets the I2C bus number /dev/i2c#
    return 1 if get_pi_revision() > 1 else 0

class PWM :
    # Registers/etc.
    __MODE1              = 0x00
    __MODE2              = 0x01
    __SUBADR1            = 0x02
    __SUBADR2            = 0x03
    __SUBADR3            = 0x04
    __PRESCALE           = 0xFE
    __LED0_ON_L          = 0x06
    __LED0_ON_H          = 0x07
    __LED0_OFF_L         = 0x08
    __LED0_OFF_H         = 0x09
    __ALL_LED_ON_L       = 0xFA
    __ALL_LED_ON_H       = 0xFB
    __ALL_LED_OFF_L      = 0xFC
    __ALL_LED_OFF_H      = 0xFD

    # Bits
    __RESTART            = 0x80
    __SLEEP              = 0x10
    __ALLCALL            = 0x01
    __INVRT              = 0x10
    __OUTDRV             = 0x04

    general_call_i2c = I2C.Device(0x00, get_pi_ic2_bus())

    @classmethod
    def software_reset(cls):
        """ Sends a software reset (SWRST) command to all the servo drivers on the bus """
        cls.general_call_i2c.writeRaw8(0x06) # SWRST

    def __init__(self, address=0x40):
        self._address = address
        self._i2c = I2C.Device(address, get_pi_ic2_bus())

        self._logger = logging.getLogger('Adafruit_Motor_Hat.PWM.{0:#0X}'.format(address))
        self._logger.info("Reseting PCA9685 MODE1 (without SLEEP) and MODE2")

        self.set_all_pwm(0, 0)
        self._i2c.write8(self.__MODE2, self.__OUTDRV)
        self._i2c.write8(self.__MODE1, self.__ALLCALL)
        time.sleep(0.005)                             # wait for oscillator

        mode1 = self._i2c.readU8(self.__MODE1)
        mode1 &= ~self.__SLEEP  # wake up (reset sleep)
        self._i2c.write8(self.__MODE1, mode1)
        time.sleep(0.005)                             # wait for oscillator

    def set_pwm_freq(self, freq):
        """ Sets the PWM frequency """
        prescaleval = 25000000.0    # 25MHz
        prescaleval /= 4096.0       # 12-bit
        prescaleval /= float(freq)
        prescaleval -= 1.0

        self._logger.info("Setting PWM frequency to {} Hz".format(freq))
        self._logger.info("Estimated pre-scale: {}".format(prescaleval))

        prescale = math.floor(prescaleval + 0.5)
        self._logger.info("Final pre-scale: {}".format(prescale))

        oldmode = self._i2c.readU8(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10             # sleep
        self._i2c.write8(self.__MODE1, newmode)        # go to sleep
        self._i2c.write8(self.__PRESCALE, int(math.floor(prescale)))
        self._i2c.write8(self.__MODE1, oldmode)
        time.sleep(0.005)
        self._i2c.write8(self.__MODE1, oldmode | 0x80)

    def set_pwm(self, channel, on, off):
        """ Sets a single PWM channel """
        self._i2c.write8(self.__LED0_ON_L + 4*channel, on & 0xFF)
        self._i2c.write8(self.__LED0_ON_H + 4*channel, on >> 8)
        self._i2c.write8(self.__LED0_OFF_L + 4*channel, off & 0xFF)
        self._i2c.write8(self.__LED0_OFF_H + 4*channel, off >> 8)

    def set_all_pwm(self, on, off):
        """ Sets a all PWM channels """
        self._i2c.write8(self.__ALL_LED_ON_L, on & 0xFF)
        self._i2c.write8(self.__ALL_LED_ON_H, on >> 8)
        self._i2c.write8(self.__ALL_LED_OFF_L, off & 0xFF)
        self._i2c.write8(self.__ALL_LED_OFF_H, off >> 8)
