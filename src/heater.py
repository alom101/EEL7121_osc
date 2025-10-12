from machine import PWM, Pin


class HeaterInterface:
    ''' Interface comum para os aquecedores '''

    def read(self) -> int:
        raise NotImplementedError()

    def write(self, value: int):
        raise NotImplementedError()


class HeaterPWM(HeaterInterface):
    ''' Implementação de um aquecedor controlado por PWM '''

    def __init__(self, pin, pwm_freq=60, initial_value=0, invert=False):
        self.pwm = PWM(
            Pin(pin, Pin.OUT),
            freq=pwm_freq,
            duty_u16=initial_value,
            invert=invert
        )

    def read(self) -> int:
        return self.pwm.duty_u16()

    def write(self, value: int):
        self.pwm.duty_u16(int(value))


if __name__ == "__main__":
    from tests import profile

    print("Running tests for heater.py")

    heater = HeaterPWM(25)
    profile([
        {
            'func_name': "HeaterPWM.write",
            'func': heater.write,
            'kwargs': {
                'value': 10_000
            }
        }, {
            'func_name': "HeaterPWM.read",
            'func': heater.read,
        }
    ])
