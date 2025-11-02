from temperature_sensor import SensorThermistorRseriesV2, SensorThermistorRseries
from heater import HeaterPWM
from strategy import StrategyOnOff
from thermal_controller import ThermalController
from frequency_sensor import FreqSensorPIO
from data_history import DataHistory
from tests import Clock

from machine import Pin
from time import sleep

# block restart
# Isso impede que o programa entre em um loop e não deixe atualizar
import os
if 'history.csv' in os.listdir():
    print("Delete 'history.csv' to continue!")
    exit()
#

CONFIG = "Arthur"
# CONFIG = "Thales"


ssid = 'Andrio2'
password = 'ufsc202502'

HEATER_PWM_PIN = 16
THERMISTOR_ADC_PIN = 27
FREQUENCY_PIN = 15
TARGET_TEMP_INITIAL = 45.0
DATA_HISTORY_PERIOD = 60 # segundos

if CONFIG == 'Arthur':
    R_SERIES = 10_000
    temp_sensor = SensorThermistorRseriesV2(THERMISTOR_ADC_PIN, R_SERIES)
    fake_osc = Clock(14, 455_000)
    RUN_WEBSERVER = False

elif CONFIG == "Thales":
    R_SERIES = 14.8
    temp_sensor = SensorThermistorRseries(THERMISTOR_ADC_PIN, R_SERIES, 38.701, -8.882)
    RUN_WEBSERVER = True


freq_counter = FreqSensorPIO(FREQUENCY_PIN, count_to=100_000)
heater = HeaterPWM(HEATER_PWM_PIN, pwm_freq=60,
                       initial_value=0, invert=True)
controller_strategy = StrategyOnOff()

thermal_controller = ThermalController(
    temp_sensor,
    heater,
    controller_strategy,
    target=TARGET_TEMP_INITIAL,
)

data_history = DataHistory(freq_counter, temp_sensor,
                           heater, thermal_controller, sample_period=DATA_HISTORY_PERIOD)



try:
    led = Pin("LED", Pin.OUT)
    if RUN_WEBSERVER:
        for _ in range(10):
            led.toggle()
            sleep(0.2)
    else:
        print("timestamp\tfreq\ttemp\tpwm\ttarget")
        while True:
            led.toggle()
            print(f"{data_history.timestamp:^5}\t{data_history.freq:^5.2f}\t{data_history.temp:^5.2f}\t{
                  data_history.heater:^5}\t{data_history.target_temp:^5.2f}")
            sleep(0.2)

    from web_server import WebServer
    server = WebServer(data_history, ssid, password)

    ip = server.connect()
    connection = server.open_socket(ip)

    server.serve(connection)
except KeyboardInterrupt:
    print('Sistema interrompido. Desligando aquecedor.')
    thermal_controller.stop()
    data_history.stop()
    heater.write(0)
except RuntimeError as e:
    print(f"ERRO CRÍTICO NA INICIALIZAÇÃO: {e}")
    heater.write(0)
