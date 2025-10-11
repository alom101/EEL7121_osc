from heater import HeaterInterface
from sensor_temp import SensorInterface
from strategy import StrategyInterface
from machine import Timer


class ThermalController:
    def __init__(self, temperature_sensor:SensorInterface, heater:HeaterInterface, strategy:StrategyInterface, target=0, update_freq=1_000):
        self.sensor = temperature_sensor
        self.actuator = heater
        self.strategy = strategy
        self.target = target
        self.timer = Timer()
        self.timer.init(freq=update_freq, callback=self.update)

    def set_target(self, new_target):
        self.target = new_target

    def update(self, t):
        sensor_reading = self.sensor.read()
        strategy_output = self.strategy.update(sensor_reading, self.target)
        self.actuator.write(strategy_output)


if __name__=="__main__":
    from random import getrandbits
    from heater import HeaterPWM
    from temperature_sensor import SensorTimeConstant, SensorADC
    from strategy import StrategyOnOff, StrategyP

    heater = HeaterPWM(19)
    
    # sensor = SensorTimeConstant(26)
    sensor = SensorADC(26)

    #strategy = StrategyOnOff()
    strategy = StrategyP(Kp=500)

    controller = ThermalController(sensor, heater, strategy)

    from time import sleep
    while True:
        for _ in range(20):
            print(f'Sensor:{sensor.read()}\tHeater:{heater.read()}\tTarget:{controller.target}')
            #print(f'Sensor:{sensor.read()}\tHeater:{controller.target}')
            sleep(0.1)
        controller.set_target(getrandbits(16))
