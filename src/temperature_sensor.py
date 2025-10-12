from machine import Pin, ADC, Timer
from onewire import OneWire
from ds18x20 import DS18X20
from time import ticks_us
from math import log, exp


class TempSensorInterface:
    ''' Interface for the temperature sensor '''

    def read(self):
        ''' This MUST return the temperature '''
        raise NotImplementedError()


class SensorThermistorRseries:
    ''' A thermistor in series with a resistor being read by the adc'''

    def __init__(self, adc_pin, r_series, A, B):
        self.adc = ADC(Pin(adc_pin))
        self.r_series = r_series
        self.A = A
        self.B = B

    def resistance_to_temperature(self, resistance):
        return self.A + self.B*log(resistance)

    def temperature_to_resistance(self, temperature):
        return exp((temperature-self.A)/self.B)

    def adc_to_resistance(self, adc_read):
        return (self.r_series*(2**16-1))/adc_read - self.r_series

    def resistance_to_adc(self, resistance):
        return (2**16-1)/(resistance/self.r_series + 1)

    def read(self):
        return self.resistance_to_temperature(self.adc_to_resistance(self.adc.read_u16()))


class SensorTimeConstant(TempSensorInterface):
    def __init__(self, input_pin, output_pin):
        print("AVISO: a classe SensorTimeConstant não retorna a temperatura como determinado pela interface!")
        self.input_pin = Pin(input_pin, Pin.IN, Pin.PULL_UP)
        self.output_pin = Pin(output_pin, Pin.OUT)
        self.output_pin(False)
        self.t_up = 0
        self.t_down = 0
        self.t_delta = 0
        self.input_pin.irq(handler=self.on_pin_change,
                           trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING)
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


class SensorDS18B20(TempSensorInterface):
    def __init__(self, pin):
        self.ds = DS18X20(OneWire(Pin(pin)))
        self.rom = self.ds.scan()[0]
        self.last_read = 0
        self.start_read_timer = Timer()
        self.finish_read_timer = Timer()
        self.start_read_timer.init(freq=1, callback=self.start_read)

    def start_read(self, t):
        self.ds.convert_temp()
        self.finish_read_timer.init(mode=Timer.ONE_SHOT, period=750, callback=self.finish_read)

    def finish_read(self, t):
        self.last_read = self.ds.read_temp(self.rom)

    def read(self):
        return self.last_read


if __name__ == "__main__":
    from time import sleep

    # sensor = SensorThermistorRseries(27, 10_000, A=38.701, B=-8.882)
    sensor = SensorDS18B20(4)

    while (True):
        T = sensor.read()
        #print(f"T:{T}\tR:{sensor.temperature_to_resistance(T)}")
        print(f"T:{T}")
        sleep(0.2)
