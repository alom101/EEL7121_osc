from machine import Pin, ADC
from time import ticks_us


class SensorInterface:
    def read(self):
        raise NotImplementedError()


class SensorADC:
    def __init__(self, pin):
        self.adc = ADC(Pin(pin))

    def read(self):
        return self.adc.read_u16()


class SensorTimeConstant:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.t_up = ticks_us()
        self.t_down = ticks_us()
        self.pin.irq(handler=self.on_pin_change, trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING)

    def on_pin_change(self, pin):
        if pin():
            print("UP")
            self.t_up = ticks_us()
        else:
            print("DOWN")
            self.t_down = ticks_us()

    def read(self):
        return abs(self.t_up - self.t_down)


if __name__=="__main__":
    from time import sleep
    s = SensorTimeConstant(24)

    while(True):
        print(s.read())
        sleep(1)
