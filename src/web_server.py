import network
import socket
import sys
import json
from time import sleep, ticks_us
from machine import Pin, ADC, Timer, PWM
from math import log, exp, sqrt
from rp2 import StateMachine, asm_pio

ssid = 'Andrio2'
password = 'ufsc202502'


HEATER_PWM_PIN = 15      
THERMISTOR_ADC_PIN = 27
FREQUENCY_PIN = 26       


R_SERIES = 10_000

A_TERM = 38.701
B_TERM = -8.882

TARGET_TEMP_INITIAL = 50.0 
KP = 500
KI = 0.1
UPDATE_FREQ_HZ = 10

from temperature_sensor import SensorThermistorRseriesV2
from heater import HeaterPWM
from strategy import StrategyOnOff
from thermal_controller import ThermalController
from frequency_sensor import FreqSensorPIO

# class TempSensorInterface:
#     def read(self):
#         raise NotImplementedError()
#
# class SensorThermistorRseries(TempSensorInterface):
#     # logR = A + B*log(R)
#     def __init__(self, adc_pin, r_series, A, B):
#         self.adc = ADC(Pin(adc_pin))
#         self.r_series = r_series
#         self.A = A
#         self.B = B
#
#     def resistance_to_temperature(self, resistance):
#         return self.A + self.B*log(resistance)
#
#     def adc_to_resistance(self, adc_read):
#         return (self.r_series*(2**16-1))/adc_read - self.r_series
#
#     def read(self):
#         try:
#             r = self.adc_to_resistance(self.adc.read_u16())
#             temp = self.resistance_to_temperature(r)
#             return round(temp, 2)
#         except Exception:
#             return 0.0
#
#
# class HeaterInterface:
#     def read(self) -> int:
#         raise NotImplementedError()
#     def write(self, value: int):
#         raise NotImplementedError()
#
# class HeaterPWM(HeaterInterface):
#     def __init__(self, pin, pwm_freq=60, initial_value=0, invert=False):
#         self.pwm = PWM(Pin(pin, Pin.OUT), freq=pwm_freq, duty_u16=initial_value, invert=invert)
#     def read(self) -> int:
#         return self.pwm.duty_u16()
#     def write(self, value: int):
#         self.pwm.duty_u16(int(value))
#
#
# class StrategyInterface:
#     def update(self, current_value, target):
#         raise NotImplementedError()
#
# class StrategyPI(StrategyInterface):
#     def __init__(self, Kp=10, Ki=0.1, integral_limit=65535):
#         self.Kp = Kp
#         self.Ki = Ki
#         self.integral = 0.0
#         self.integral_limit = integral_limit
#         self.max_output = 2**16
#
#     def update(self, current_value, target):
#         error = target - current_value
#         P = error * self.Kp
#
#         self.integral += error * self.Ki
#         self.integral = max(min(self.integral, self.integral_limit), 0)
#
#         output = P + self.integral
#
#         output = max(min(output, self.max_output), 0)
#
#         return output
#
# class ThermalController:
#     def __init__(self, temperature_sensor:TempSensorInterface, heater:HeaterInterface, strategy:StrategyInterface, target=0, update_freq=10):
#         self.sensor = temperature_sensor
#         self.actuator = heater
#         self.strategy = strategy
#         self.target = target
#         self.timer = Timer()
#         self.timer.init(freq=update_freq, callback=self.update)
#
#     def set_target(self, new_target):
#         self.target = new_target
#
#     def update(self, t):
#         sensor_reading = self.sensor.read()
#         strategy_output = self.strategy.update(sensor_reading, self.target)
#         self.actuator.write(strategy_output)
#
# class FreqSensorInterface:
#     @property
#     def frequency(self):
#         raise NotImplementedError()
#
# class FreqSensorPulseCounter(FreqSensorInterface):
#     def __init__(self, pin, measure_freq=1.0):
#         self.pin = Pin(pin, Pin.IN)
#         self.pin.irq(handler=self.count_pulse_callback, trigger=Pin.IRQ_RISING)
#         self.timer = Timer()
#         self.measure_freq = measure_freq
#         # O timer dispara a cada segundo
#         self.timer.init(freq=int(measure_freq), callback=self.finish_callback) 
#         self.pulse_counter = 0
#         self._freq = 0
#
#     @property
#     def frequency(self):
#         return self._freq
#
#     def finish_callback(self, t):
#         # Calcula freq (Hz) = Pulsos / tempo de medição (1/measure_freq)
#         self._freq = self.pulse_counter * self.measure_freq
#         self.pulse_counter = 0
#
#     def count_pulse_callback(self, pin):
#         self.pulse_counter += 1
#
#
temp_sensor = SensorThermistorRseriesV2(THERMISTOR_ADC_PIN, R_SERIES)
freq_counter = FreqSensorPIO(FREQUENCY_PIN, count_to=100_000)
heater = HeaterPWM(HEATER_PWM_PIN, pwm_freq=60, initial_value=0)
controller_strategy = StrategyOnOff() 

thermal_controller = ThermalController(
    temp_sensor, 
    heater, 
    controller_strategy, 
    target=TARGET_TEMP_INITIAL, 
    update_freq=UPDATE_FREQ_HZ 
)

led = Pin("LED", Pin.OUT)
led.off()

def connect():
    """Configura o Pico W como Ponto de Acesso (AP) e retorna o IP."""
    wlan = network.WLAN(network.AP_IF)
    wlan.config(essid=ssid, password=password)
    wlan.active(True)
    
    max_wait = 10
    while wlan.active() == False and max_wait > 0:
        print('Aguardando ativação do AP...')
        led.value(not led.value())
        max_wait -= 1
        sleep(0.5)
        
    led.off()
    if not wlan.active():
        raise RuntimeError('Falha na ativação do Ponto de Acesso.')
        
    ip = wlan.ifconfig()[0]
    print(f'Ponto de Acesso "{ssid}" criado com sucesso.')
    print(f'Acesse o dashboard em: http://{ip}')
    return ip


def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection.bind(address)
    connection.listen(5)
    return connection


def web_page_dashboard(controller_inst, freq_inst):
    """Gera o HTML do dashboard com dados em tempo real."""
    temp_atual = controller_inst.sensor.read()
    temp_alvo = controller_inst.target
    freq_oscilacao_hz = freq_inst.frequency
    potencia = controller_inst.actuator.read()
    
    
    potencia_perc = (potencia / 65535) * 100
    
    if abs(temp_atual - temp_alvo) < 0.5:
        temp_status = "ESTÁVEL (±0.5°C)"
        status_color = "#d4edda" 
    else:
        temp_status = "AJUSTANDO"
        status_color = "#fff3cd" 
        
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Dashboard CRB455B</title>
        <meta http-equiv="refresh" content="3"> <style>
            body {{ font-family: Arial, sans-serif; background: #f4f6f9; text-align: center; }}
            .container {{ margin: 20px auto; max-width: 500px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }}
            .data-box {{ margin: 15px 0; padding: 15px; border-radius: 8px; font-size: 18px; border: 1px solid #ccc; }}
            .status {{ background: {status_color}; font-weight: bold; border-color: #0077b6; }}
            input[type=number] {{ padding: 10px; border: 1px solid #ccc; border-radius: 5px; }}
            button {{ padding: 10px 20px; background: #0077b6; color: white; border: none; border-radius: 5px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Monitor de Estabilidade Térmica</h1>

            <div class="data-box status">
                <strong>STATUS:</strong> {temp_status}
            </div>

            <div class="data-box">
                Temperatura Alvo: <strong>{temp_alvo:.1f} °C</strong>
            </div>

            <div class="data-box">
                Temperatura Atual: <strong>{temp_atual:.2f} °C</strong>
            </div>
            
            <div class="data-box">
                Frequência de Oscilação: <strong>{freq_oscilacao_hz / 1000:.3f} kHz</strong>
            </div>
            
            <div class="data-box">
                Potência do Aquecedor (PWM): <strong>{potencia_perc:.1f} %</strong>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def serve(connection):
    """Loop principal do servidor que aceita requisições e processa o formulário."""
    while True:
        client = None
        try:
            client = connection.accept()[0]
            request = client.recv(1024).decode()
            
            if request.split('\r\n')[0].startswith('GET /?target='):
                try:
                    params = request.split('\r\n')[0].split('?')[1].split('&')
                    for param in params:
                        if param.startswith('target='):
                            new_target = float(param.split('=')[1])
                            thermal_controller.set_target(new_target)
                            print(f"ALVO ATUALIZADO: {new_target:.1f}°C")
                            break
                except Exception:
                    pass
                        
            html = web_page_dashboard(thermal_controller, freq_counter)
            
            client.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\nConnection: close\r\n\r\n')
            client.send(html)
            
        except OSError:
            # Erro de socket, fecha o cliente e continua
            pass
        except Exception as e:
            # print(f'Erro inesperado no servidor: {e}')
            pass
        finally:
            if client:
                client.close()

if __name__ == "__main__":
    try:
        ip = connect()
        connection = open_socket(ip)

        serve(connection) 
    except KeyboardInterrupt:
        print('Sistema interrompido. Desligando aquecedor.')
        heater.write(0) 
    except RuntimeError as e:
        print(f"ERRO CRÍTICO NA INICIALIZAÇÃO: {e}")
        heater.write(0)
