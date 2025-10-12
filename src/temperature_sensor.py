from machine import Pin, ADC
from time import ticks_us


class TempSensorInterface:
    ''' Interface for the temperature sensor '''

    def read(self):
        ''' This MUST return the temperature '''
        raise NotImplementedError()


class SensorResistanceDivider(TempSensorInterface):
    def __init__(self, pin, r_series):
        self.adc = ADC(Pin(pin))
        self.r_series = r_series

    def read(self):
        v = self.adc.read_u16()/(2**16-1)*3.3
#        print("RESISTANCE DIVIDER INCOMPLETE!")
        return v


class SensorTimeConstant(TempSensorInterface):
    def __init__(self, input_pin, output_pin):
        print("AVISO: a classe SensorTimeConstant não retorna a temperatura como determinado pela interface!")
        self.input_pin = Pin(input_pin, Pin.IN, Pin.PULL_UP)
        self.output_pin = Pin(output_pin, Pin.OUT)
        self.output_pin(False)
        self.t_up = 0
        self.t_down = 0
        self.t_delta = 0
        self.input_pin.irq(handler=self.on_pin_change, trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING)
        self.output_pin(True)

    def on_pin_change(self, pin):
        if pin():
            self.t_up = ticks_us()
            self.output_pin(False)
        else:
            self.t_down = ticks_us()
            self.output_pin(True)
            self.t_delta = abs(self.t_up - self.t_down)

    def read(self):
        return self.t_delta


if __name__=="__main__":
    from time import sleep
    # s = SensorTimeConstant(input_pin=14, output_pin=15)
    s = SensorADC(26)

    while(True):
        print(s.read())
        sleep(1)
