from machine import Timer
from frequency_sensor import FreqSensorInterface
from temperature_sensor import TempSensorInterface
from heater import HeaterInterface
from thermal_controller import ThermalController
from time import time

class DataHistory:
    
    def __init__(
            self,
            frequency_sensor: FreqSensorInterface,
            temperature_sensor: TempSensorInterface,
            heater: HeaterInterface,
            controller: ThermalController,
            sample_period=60
            ):
        self._start_time = time()
        self._frequency_sensor = frequency_sensor
        self._temperature_sensor = temperature_sensor
        self._heater = heater
        self._sample_period = sample_period
        self._controller = controller

        self.timestamp = 0
        self.freq = 0
        self.temp = 0
        self.heater = 0
        self.target_temp = 0
        self._timer = Timer()

        self.start()

    def start(self):
        self._timer.init(period=self.sample_period, callback=self._read_sensors_callback, hard=False)

    def stop(self):
        self._timer.deinit()

    def _read_sensors_callback(self, timer):
        self.timestamp = time() - self._start_time
        self.freq = self._frequency_sensor.frequency
        self.temp = self._temperature_sensor.read()
        self.heater = self._heater.read()
        self.target_temp = self._controller.target
        self._save_data()

    def _save_data(self):
        with open("history.csv", 'at') as file:
            file.write(f"\n{self.timestamp},{self.freq},{self.temp},{self.heater},{self.target_temp}")
