from heater import HeaterInterface
from temperature_sensor import TempSensorInterface
from strategy import StrategyInterface
from machine import Timer
from data_history import DataHistory

class ThermalController:
    def __init__(self, temperature_sensor:SensorInterface, heater:HeaterInterface, strategy:StrategyInterface, target=0, update_freq=1_000, history_size=40):
        # adicionar no init -> history_size=40
        self.sensor = temperature_sensor
        self.actuator = heater
        self.strategy = strategy
        self.target = target
        self.timer = Timer()
        self.timer.init(freq=update_freq, callback=self.update)
        self.temp_history = DataHistory(history_size)

    def set_target(self, new_target):
        self.target = new_target

    def update(self, t):
        sensor_reading = self.sensor.read()
        strategy_output = self.strategy.update(sensor_reading, self.target)
        self.actuator.write(strategy_output)
        self.temp_history.add_point(sensor_reading)


if __name__=="__main__":
    from random import getrandbits
    from heater import HeaterPWM
    from temperature_sensor import SensorTimeConstant, SensorThermistorRseries
    from strategy import StrategyOnOff, StrategyP

    heater = HeaterPWM(19)
    
    # sensor = SensorTimeConstant(26)
    sensor = SensorThermistorRseries(27, 10_000, A=38.701, B=-8.882)

    #strategy = StrategyOnOff()
    strategy = StrategyP(Kp=500)

    controller = ThermalController(sensor, heater, strategy)
    controller.set_target(-45)

    from time import sleep
    while True:
        for _ in range(20):
            #print(f'Sensor:{sensor.read():.2f}\tHeater:{heater.read():.2f}\tTarget:{controller.target:.2f}')
            print(f'Sensor:{sensor.read()}\tHeater:{controller.target}')
            sleep(0.1)
        controller.set_target(getrandbits(16))
