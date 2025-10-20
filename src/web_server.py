import network
import socket
from machine import Pin

from temperature_sensor import SensorThermistorRseriesV2
from heater import HeaterPWM
from strategy import StrategyOnOff
from thermal_controller import ThermalController
from frequency_sensor import FreqSensorPIO
from tests import Clock



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
heater = HeaterPWM(HEATER_PWM_PIN, pwm_freq=60, initial_value=0)
controller_strategy = StrategyOnOff() 
fake_oscilator = Clock(FAKE_OSCILATOR_PIN, 455_000)

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
    from time import sleep

    for _ in range(20):
        print(f"freq:{freq_counter.frequency}\ttemp:{temp_sensor.read()}")
        sleep(1)

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
