from heater import Heater
from temperature_sensor import TemperatureSensor

class ThermalController:
    def __init__(self, temperature_sensor:TemperatureSensor, heater:Heater, target=50):
        self.sensor = temperature_sensor
        self.actuator = heater
        self.target = target

    def set_target(self, value):
        self.target = target

    def update(self):
        if(self.sensor.read_temperature() < self.target):
            self.actuator.on()
        else:
            self.actuator.off()
