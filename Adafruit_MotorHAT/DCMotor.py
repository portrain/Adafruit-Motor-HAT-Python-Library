
class DCMotorConfig(object):
    def __init__(self, pwm, in1, in2):
        self.pwm = pwm
        self.in1 = in1
        self.in2 = in2

MOTORS = [
    DCMotorConfig(pwm=8, in1=10, in2=9),
    DCMotorConfig(pwm=13, in1=11, in2=12),
    DCMotorConfig(pwm=2, in1=4, in2=3),
    DCMotorConfig(pwm=7, in1=5, in2=6)
]


class DCMotor(object):
    FORWARD = 1
    BACKWARD = 2
    BRAKE = 3
    RELEASE = 4

    def __init__(self, controller, motor_number):
        motor_number -= 1
        if motor_number <0 or motor_number > len(MOTORS):
            raise RuntimeError('MotorHAT Motor must be between 1 and 4 inclusive')

        self._controller = controller
        self._config = MOTORS[motor_number]

    def run(self, command):
        if command == self.FORWARD:
            self._controller.set_pin(self._config.in2, 0)
            self._controller.set_pin(self._config.in1, 1)
        elif command == self.BACKWARD:
            self._controller.set_pin(self._config.in1, 0)
            self._controller.set_pin(self._config.in2, 1)
        elif command == self.RELEASE:
            self._controller.set_pin(self._config.in1, 0)
            self._controller.set_pin(self._config.in2, 0)

    def set_speed(self, speed):
        self._controller.set_pwm(self._config.pwm, 0,
                                 min(255, max(0, speed)) * 16)
