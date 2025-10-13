from machine import Pin, ADC, Timer
from onewire import OneWire
from ds18x20 import DS18X20
from time import ticks_us
from math import log, exp, sqrt
import json


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


class SensorThermistorRseriesV2:
    ''' A thermistor in series with a resistor being read by the adc'''

    def __init__(self, adc_pin, r_series, params_file="thermistor_params.json"):
        self.adc = ADC(Pin(adc_pin))
        self.r_series = r_series
        with open(params_file, "rt") as file:
            params = json.load(file)
        self.A = float(params['steinhart-hart']['A'])
        self.B = float(params['steinhart-hart']['B'])
        self.C = float(params['steinhart-hart']['C'])

    def resistance_to_temperature(self, resistance):
        logR = log(resistance)
        return 1/(self.A + self.B*logR + self.C*(logR)**3)

    def temperature_to_resistance(self, temperature):
        x = (self.A - 1/temperature)/self.C
        y = sqrt((self.B/(3*self.C)**3) + x**2/4)
        return exp((y-x/2)**(1/3) - (y+x/2)**1/3)

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
    def __init__(self, pin, sample_period_ms=1000):
        self.ds = DS18X20(OneWire(Pin(pin)))
        self.rom = self.ds.scan()[0]
        self.last_read = 0
        self.timer = Timer()
        self.timer.init(period=sample_period_ms, callback=self._read_onewire)
        self.ds.convert_temp()

    def _read_onewire(self, t):
        self.last_read = self.ds.read_temp(self.rom)
        self.ds.convert_temp()

    def read(self):
        return self.last_read
    


if __name__ == "__main__":
    from time import sleep
    
    # thermistor = SensorThermistorRseriesV2(27, 10_000)
    thermistor_1 = SensorThermistorRseriesV2(27, 10_000, params_file="thermistor_params_v1.json")
    thermistor_2 = SensorThermistorRseriesV2(27, 10_000, params_file="thermistor_params_v2.json")
    thermistor_3 = SensorThermistorRseriesV2(27, 10_000, params_file="thermistor_params_v3.json")
    ds18b20 = SensorDS18B20(4)

    sleep(1)
    
    while (True):
        print(f"Termistor(v1):{thermistor_1.read():.2f}\tTermistor(v2):{thermistor_2.read():.2f}\tTermistor(v3):{thermistor_3.read():.2f}\tDS18B20:{ds18b20.read():.2f}")
        sleep(1)
