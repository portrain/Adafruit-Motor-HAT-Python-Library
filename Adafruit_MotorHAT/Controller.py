from Adafruit_PCA9685 import PCA9685


class Controller(object):

    def __init__(self, address=0x60, frequency=1600):
        self._address = address      # default addr on HAT
        self._frequency = frequency  # default @1600Hz PWM freq

        self._pwm = PCA9685(address)
        self._pwm.set_pwm_freq(self._frequency)

    def set_pin(self, pin, value):
        if (pin < 0) or (pin > 15):
            raise NameError('PWM pin must be between 0 and 15 inclusive')
        if (value != 0) and (value != 1):
            raise NameError('Pin value must be 0 or 1!')
        if value == 0:
            self._pwm.set_pwm(pin, 0, 4096)
        if value == 1:
            self._pwm.set_pwm(pin, 4096, 0)

    def set_pwm(self, channel, on, off):
        self._pwm.set_pwm(channel, on, off)
