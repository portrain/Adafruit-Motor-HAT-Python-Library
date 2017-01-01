import time


class StepperMotorConfig(object):
    def __init__(self, a_pwm, a_in1, a_in2, b_pwm, b_in1, b_in2):
        self.a_pwm = a_pwm
        self.a_in1 = a_in1
        self.a_in2 = a_in2
        self.b_pwm = b_pwm
        self.b_in1 = b_in1
        self.b_in2 = b_in2

MOTORS = [
    StepperMotorConfig(a_pwm=8, a_in1=10, a_in2=9, b_pwm=13, b_in1=11, b_in2=12),
    StepperMotorConfig(a_pwm=2, a_in1=4, a_in2=3, b_pwm=7, b_in1=5, b_in2=6)
]

MICROSTEPS = 8
MICROSTEP_CURVE = [0, 50, 98, 142, 180, 212, 236, 250, 255]

# MICROSTEPS = 16
# a sinusoidal curve NOT LINEAR!
# MICROSTEP_CURVE = [0, 25, 50, 74, 98, 120, 141, 162, 180, 197, 212, 225, 236, 244, 250, 253, 255]


class StepperMotor(object):
    FORWARD = 1
    BACKWARD = 2
    SINGLE = 1
    DOUBLE = 2
    INTERLEAVE = 3
    MICROSTEP = 4

    def __init__(self, controller, motor_number, steps=200):
        motor_number -= 1
        if motor_number < 0 or motor_number > len(MOTORS):
            raise RuntimeError('MotorHAT Motor must be between 1 and {} inclusive'.format(len(MOTORS)))

        self._controller = controller
        self._steps = steps
        self._config = MOTORS[motor_number]

        self._sec_per_step = 0.1
        self._stepping_counter = 0
        self._current_step = 0

    def set_speed(self, rpm):
        self._sec_per_step = 60.0 / (self._steps * rpm)
        self._stepping_counter = 0

    def one_step(self, direction, style):
        pwm_a = pwm_b = 255

        # first determine what sort of stepping procedure we're up to
        if style == self.SINGLE:
            if (self._current_step // (MICROSTEPS // 2)) % 2:
                # we're at an odd step, weird
                if direction == self.FORWARD:
                    self._current_step += MICROSTEPS // 2
                else:
                    self._current_step -= MICROSTEPS // 2
            else:
                # go to next even step
                if direction == self.FORWARD:
                    self._current_step += MICROSTEPS
                else:
                    self._current_step -= MICROSTEPS

        elif style == self.DOUBLE:
            if not (self._current_step // (MICROSTEPS // 2) % 2):
                # we're at an even step, weird
                if direction == self.FORWARD:
                    self._current_step += MICROSTEPS // 2
                else:
                    self._current_step -= MICROSTEPS // 2
            else:
                # go to next odd step
                if direction == self.FORWARD:
                    self._current_step += MICROSTEPS
                else:
                    self._current_step -= MICROSTEPS

        elif style == self.INTERLEAVE:
            if direction == self.FORWARD:
                self._current_step += MICROSTEPS // 2
            else:
                self._current_step -= MICROSTEPS // 2

        elif style == self.MICROSTEP:
            if direction == self.FORWARD:
                self._current_step += 1
            else:
                self._current_step -= 1

                # go to next 'step' and wrap around
                self._current_step += MICROSTEPS * 4
                self._current_step %= MICROSTEPS * 4

            pwm_a = pwm_b = 0
            if (self._current_step >= 0) and (self._current_step < MICROSTEPS):
                pwm_a = MICROSTEP_CURVE[MICROSTEPS - self._current_step]
                pwm_b = MICROSTEP_CURVE[self._current_step]
            elif (self._current_step >= MICROSTEPS) and (self._current_step < MICROSTEPS * 2):
                pwm_a = MICROSTEP_CURVE[self._current_step - MICROSTEPS]
                pwm_b = MICROSTEP_CURVE[MICROSTEPS * 2 - self._current_step]
            elif (self._current_step >= MICROSTEPS * 2) and (self._current_step < MICROSTEPS * 3):
                pwm_a = MICROSTEP_CURVE[MICROSTEPS * 3 - self._current_step]
                pwm_b = MICROSTEP_CURVE[self._current_step - MICROSTEPS * 2]
            elif (self._current_step >= MICROSTEPS * 3) and (self._current_step < MICROSTEPS * 4):
                pwm_a = MICROSTEP_CURVE[self._current_step - MICROSTEPS * 3]
                pwm_b = MICROSTEP_CURVE[MICROSTEPS * 4 - self._current_step]


        # go to next 'step' and wrap around
        self._current_step += MICROSTEPS * 4
        self._current_step %= MICROSTEPS * 4

        # only really used for microstepping, otherwise always on!
        self._controller.set_pwm(self._config.a_pwm, 0, pwm_a*16)
        self._controller.set_pwm(self._config.b_pwm, 0, pwm_b*16)

        # set up coil energizing!
        coils = [0, 0, 0, 0]

        if style == self.MICROSTEP:
            if (self._current_step >= 0) and (self._current_step < MICROSTEPS):
                coils = [1, 1, 0, 0]
            elif (self._current_step >= MICROSTEPS) and (self._current_step < MICROSTEPS * 2):
                coils = [0, 1, 1, 0]
            elif (self._current_step >= MICROSTEPS*2) and (self._current_step < MICROSTEPS * 3):
                coils = [0, 0, 1, 1]
            elif (self._current_step >= MICROSTEPS*3) and (self._current_step < MICROSTEPS * 4):
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
            coils = step2coils[self._current_step // (MICROSTEPS // 2)]

        self._controller.set_pin(self._config.a_in2, coils[0])
        self._controller.set_pin(self._config.b_in1, coils[1])
        self._controller.set_pin(self._config.a_in1, coils[2])
        self._controller.set_pin(self._config.b_in2, coils[3])

        return self._current_step

    def step(self, steps, direction, style):
        s_per_s = self._sec_per_step
        latest_step = 0

        if style == self.INTERLEAVE:
            s_per_s /= 2.0
        elif style == self.MICROSTEP:
            s_per_s /= MICROSTEPS
            steps *= MICROSTEPS

        for s in range(steps):
            latest_step = self.one_step(direction, style)
            time.sleep(s_per_s)

        if style == self.MICROSTEP:
            # this is an edge case, if we are in between full steps, lets just keep going
            # so we end on a full step
            while (latest_step != 0) and (latest_step != MICROSTEPS):
                latest_step = self.one_step(dir, style)
                time.sleep(s_per_s)

    def stop(self):
        self._controller.set_pin(self._config.a_in1, 0)
        self._controller.set_pin(self._config.a_in2, 0)
        self._controller.set_pin(self._config.b_in1, 0)
        self._controller.set_pin(self._config.b_in2, 0)
