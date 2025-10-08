from heater import HeaterInterface
from temperature_sensor import SensorInterface
from machine import Timer


class ThermalController:
    def __init__(self, temperature_sensor:SensorInterface, heater:HeaterInterface, target=50, update_freq=1_000):
        self.sensor = temperature_sensor
        self.actuator = heater
        self.target = target
        self.timer = Timer()
        self.timer.init(freq=update_freq, callback=self.update)

    def update(self, t):
        if(self.sensor.read() < self.target):
            self.actuator.write(2**16)
        else:
            self.actuator.write(0)


if __name__=="__main__":
    from heater import HeaterPWM
    from temperature_sensor import SensorTimeConstant

    heater = HeaterPWM(25)
    sensor = SensorTimeConstant(24)
    controller = ThermalController(sensor, heater, 200_000)

    from time import sleep
    while True:
        value = sensor.read()
        print(value,'\t',200_000)
        sleep(1)
