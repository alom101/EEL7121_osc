from sensor_temp import SensorInterface
from math import log

class Thermistor:
    def __init__(self, sensor, r_series, A=38.701, B=-8.882):
        self.sensor = sensor
        self.r_series = r_series
        self.A = A
        self.B = B
    
    @property
    def resistance(self):
        vadc = 3.3*self.sensor.read()/(2**16-1)
        return self.r_series*(3.3/vadc -1)
    
    @property
    def temperature(self):
        return self.A + self.B*log(self.resistance)
    
    
