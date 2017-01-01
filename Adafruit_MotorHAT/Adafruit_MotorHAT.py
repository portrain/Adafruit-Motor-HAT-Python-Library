import time
import logging

from Adafruit_PCA9685 import PCA9685


class AdafruitStepperMotor(object):
    MICROSTEPS = 8
    MICROSTEP_CURVE = [0, 50, 98, 142, 180, 212, 236, 250, 255]

    #MICROSTEPS = 16
    # a sinusoidal curve NOT LINEAR!
    #MICROSTEP_CURVE = [0, 25, 50, 74, 98, 120, 141, 162, 180, 197, 212, 225, 236, 244, 250, 253, 255]

    def __init__(self, controller, num, steps=200):
        self.MC = controller
        self.rev_steps = steps
        self.motor_num = num
        self.sec_per_step = 0.1
        self.stepping_counter = 0
        self.current_step = 0

        self._logger = logging.getLogger('Adafruit_Stepper_Motor')

        num -= 1

        if num == 0:
            self.PWMA = 8
            self.AIN2 = 9
            self.AIN1 = 10
            self.PWMB = 13
            self.BIN2 = 12
            self.BIN1 = 11
        elif num == 1:
            self.PWMA = 2
            self.AIN2 = 3
            self.AIN1 = 4
            self.PWMB = 7
            self.BIN2 = 6
            self.BIN1 = 5
        else:
            raise NameError('MotorHAT Stepper must be between 1 and 2 inclusive')

    def set_speed(self, rpm):
        self.sec_per_step = 60.0 / (self.rev_steps * rpm)
        self.stepping_counter = 0

    def one_step(self, direction, style):
        pwm_a = pwm_b = 255

        # first determine what sort of stepping procedure we're up to
        if style == AdafruitMotorHAT.SINGLE:
            if (self.current_step // (self.MICROSTEPS // 2)) % 2:
                # we're at an odd step, weird
                if direction == AdafruitMotorHAT.FORWARD:
                    self.current_step += self.MICROSTEPS // 2
                else:
                    self.current_step -= self.MICROSTEPS // 2
            else:
                # go to next even step
                if direction == AdafruitMotorHAT.FORWARD:
                    self.current_step += self.MICROSTEPS
                else:
                    self.current_step -= self.MICROSTEPS
        if style == AdafruitMotorHAT.DOUBLE:
            if not (self.current_step // (self.MICROSTEPS // 2) % 2):
                # we're at an even step, weird
                if direction == AdafruitMotorHAT.FORWARD:
                    self.current_step += self.MICROSTEPS // 2
                else:
                    self.current_step -= self.MICROSTEPS // 2
            else:
                # go to next odd step
                if direction == AdafruitMotorHAT.FORWARD:
                    self.current_step += self.MICROSTEPS
                else:
                    self.current_step -= self.MICROSTEPS
        if style == AdafruitMotorHAT.INTERLEAVE:
            if direction == AdafruitMotorHAT.FORWARD:
                self.current_step += self.MICROSTEPS // 2
            else:
                self.current_step -= self.MICROSTEPS // 2

        if style == AdafruitMotorHAT.MICROSTEP:
            if direction == AdafruitMotorHAT.FORWARD:
                self.current_step += 1
            else:
                self.current_step -= 1

                # go to next 'step' and wrap around
                self.current_step += self.MICROSTEPS * 4
                self.current_step %= self.MICROSTEPS * 4

            pwm_a = pwm_b = 0
            if (self.current_step >= 0) and (self.current_step < self.MICROSTEPS):
                pwm_a = self.MICROSTEP_CURVE[self.MICROSTEPS - self.current_step]
                pwm_b = self.MICROSTEP_CURVE[self.current_step]
            elif (self.current_step >= self.MICROSTEPS) and (self.current_step < self.MICROSTEPS * 2):
                pwm_a = self.MICROSTEP_CURVE[self.current_step - self.MICROSTEPS]
                pwm_b = self.MICROSTEP_CURVE[self.MICROSTEPS * 2 - self.current_step]
            elif (self.current_step >= self.MICROSTEPS * 2) and (self.current_step < self.MICROSTEPS * 3):
                pwm_a = self.MICROSTEP_CURVE[self.MICROSTEPS * 3 - self.current_step]
                pwm_b = self.MICROSTEP_CURVE[self.current_step - self.MICROSTEPS * 2]
            elif (self.current_step >= self.MICROSTEPS * 3) and (self.current_step < self.MICROSTEPS * 4):
                pwm_a = self.MICROSTEP_CURVE[self.current_step - self.MICROSTEPS * 3]
                pwm_b = self.MICROSTEP_CURVE[self.MICROSTEPS * 4 - self.current_step]


        # go to next 'step' and wrap around
        self.current_step += self.MICROSTEPS * 4
        self.current_step %= self.MICROSTEPS * 4

        # only really used for microstepping, otherwise always on!
        self.MC.set_pwm(self.PWMA, 0, pwm_a*16)
        self.MC.set_pwm(self.PWMB, 0, pwm_b*16)

        # set up coil energizing!
        coils = [0, 0, 0, 0]

        if style == AdafruitMotorHAT.MICROSTEP:
            if (self.current_step >= 0) and (self.current_step < self.MICROSTEPS):
                coils = [1, 1, 0, 0]
            elif (self.current_step >= self.MICROSTEPS) and (self.current_step < self.MICROSTEPS * 2):
                coils = [0, 1, 1, 0]
            elif (self.current_step >= self.MICROSTEPS*2) and (self.current_step < self.MICROSTEPS * 3):
                coils = [0, 0, 1, 1]
            elif (self.current_step >= self.MICROSTEPS*3) and (self.current_step < self.MICROSTEPS * 4):
                coils = [1, 0, 0, 1]
        else:
            step2coils = [
                [1, 0, 0, 0],
                [1, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 1],
                [0, 0, 0, 1],
                [1, 0, 0, 1] ]
            coils = step2coils[self.current_step // (self.MICROSTEPS // 2)]

        self.MC.set_pin(self.AIN2, coils[0])
        self.MC.set_pin(self.BIN1, coils[1])
        self.MC.set_pin(self.AIN1, coils[2])
        self.MC.set_pin(self.BIN2, coils[3])

        return self.current_step

    def step(self, steps, direction, style):
        s_per_s = self.sec_per_step
        latest_step = 0

        if style == AdafruitMotorHAT.INTERLEAVE:
            s_per_s /= 2.0

        if style == AdafruitMotorHAT.MICROSTEP:
            s_per_s /= self.MICROSTEPS
            steps *= self.MICROSTEPS

        self._logger.info('{} sec per step'.format(s_per_s))

        for s in range(steps):
            latest_step = self.one_step(direction, style)
            time.sleep(s_per_s)

        if style == AdafruitMotorHAT.MICROSTEP:
            # this is an edge case, if we are in between full steps, lets just keep going
            # so we end on a full step
            while (latest_step != 0) and (latest_step != self.MICROSTEPS):
                latest_step = self.one_step(dir, style)
                time.sleep(s_per_s)


class AdafruitDCMotor(object):
    def __init__(self, controller, num):
        self.MC = controller
        self.motor_num = num

        if num == 0:
            pwm = 8
            in2 = 9
            in1 = 10
        elif num == 1:
            pwm = 13
            in2 = 12
            in1 = 11
        elif num == 2:
            pwm = 2
            in2 = 3
            in1 = 4
        elif num == 3:
            pwm = 7
            in2 = 6
            in1 = 5
        else:
            raise NameError('MotorHAT Motor must be between 1 and 4 inclusive')

        self._pwm_pin = pwm
        self._in1_pin = in1
        self._in2_pin = in2

    def run(self, command):
        if not self.MC:
            return

        if command == AdafruitMotorHAT.FORWARD:
            self.MC.set_pin(self._in2_pin, 0)
            self.MC.set_pin(self._in1_pin, 1)
        if command == AdafruitMotorHAT.BACKWARD:
            self.MC.set_pin(self._in1_pin, 0)
            self.MC.set_pin(self._in2_pin, 1)
        if command == AdafruitMotorHAT.RELEASE:
            self.MC.set_pin(self._in1_pin, 0)
            self.MC.set_pin(self._in2_pin, 0)

    def set_speed(self, speed):
        if speed < 0:
            speed = 0
        if speed > 255:
            speed = 255
        self.MC.set_pwm(self._pwm_pin, 0, speed*16)


class AdafruitMotorHAT(object):
    FORWARD = 1
    BACKWARD = 2
    BRAKE = 3
    RELEASE = 4

    SINGLE = 1
    DOUBLE = 2
    INTERLEAVE = 3
    MICROSTEP = 4

    def __init__(self, address = 0x60, frequency = 1600):
        self._i2caddr = address          # default addr on HAT
        self._frequency = frequency        # default @1600Hz PWM freq
        self.motors = [ AdafruitDCMotor(self, m) for m in range(4) ]
        self.steppers = [ AdafruitStepperMotor(self, 1), AdafruitStepperMotor(self, 2) ]
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

    def get_stepper(self, steps, num):
        if (num < 1) or (num > 2):
            raise NameError('MotorHAT Stepper must be between 1 and 2 inclusive')
        return self.steppers[num-1]

    def get_motor(self, num):
        if (num < 1) or (num > 4):
            raise NameError('MotorHAT Motor must be between 1 and 4 inclusive')
        return self.motors[num-1]
