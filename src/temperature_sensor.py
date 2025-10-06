from machine import ADC

class TemperatureSensor:
    def __init__(self, pin, a, b):
        self.pin = ADC(pin)
        self.a = a
        self.b = b

    def read(self):
        return self.pin.read_u16() #number from 0 to 65535
    
    def read_voltage(self):
        return self.pin.read_u16()*3.3/65535

    def read_temperature(self):
        return self.a*self.read()+self.b




