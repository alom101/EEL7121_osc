from temperature_sensor import SensorThermistorRseriesV2
from heater import HeaterPWM
from strategy import StrategyOnOff
from thermal_controller import ThermalController
from frequency_sensor import FreqSensorPIO
from tests import Clock
from web_server import WebServer

from machine import Pin
from time import sleep


ssid = 'Andrio2'
password = 'ufsc202502'


HEATER_PWM_PIN = 15      
THERMISTOR_ADC_PIN = 27
FREQUENCY_PIN = 26       
FAKE_OSCILATOR_PIN = 22

R_SERIES = 10_000

TARGET_TEMP_INITIAL = 50.0 
KP = 500
KI = 0.1
UPDATE_FREQ_HZ = 10

temp_sensor = SensorThermistorRseriesV2(THERMISTOR_ADC_PIN, R_SERIES)
freq_counter = FreqSensorPIO(FREQUENCY_PIN, count_to=100_000)
heater = HeaterPWM(HEATER_PWM_PIN, pwm_freq=60, initial_value=0, invert=True)
controller_strategy = StrategyOnOff() 
fake_oscilator = Clock(FAKE_OSCILATOR_PIN, 455_000)

thermal_controller = ThermalController(
    temp_sensor, 
    heater, 
    controller_strategy, 
    target=TARGET_TEMP_INITIAL, 
    update_freq=UPDATE_FREQ_HZ 
)

server = WebServer(temp_sensor, heater, thermal_controller, freq_counter, ssid, password)



led = Pin("LED", Pin.OUT)
for _ in range(10):
    led.toggle()
    sleep(0.2)

try:
    ip = server.connect()
    connection = server.open_socket(ip)

    server.serve(connection) 
except KeyboardInterrupt:
    print('Sistema interrompido. Desligando aquecedor.')
    heater.write(0) 
except RuntimeError as e:
    print(f"ERRO CRÍTICO NA INICIALIZAÇÃO: {e}")
    heater.write(0)
