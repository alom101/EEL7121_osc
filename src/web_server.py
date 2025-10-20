import network
import socket
from machine import Pin


class WebServer:
    def __init__(self, temp_sensor, heater, thermal_controller, freq_sensor, ssid, password):
        self.temp_sensor = temp_sensor
        self.heater = heater
        self.thermal_controller = thermal_controller
        self.frequency_sensor = freq_sensor
        self.ssid = ssid
        self.password = password
        self.led = Pin("LED", Pin.OUT)
        self.led.off()

    def connect(self):
        """Configura o Pico W como Ponto de Acesso (AP) e retorna o IP."""
        wlan = network.WLAN(network.AP_IF)
        wlan.config(essid=self.ssid, password=self.password)
        wlan.active(True)

        max_wait = 10
        while wlan.active() == False and max_wait > 0:
            print('Aguardando ativação do AP...')
            self.led.value(not self.led.value())
            max_wait -= 1
            sleep(0.5)

        self.led.off()
        if not wlan.active():
            raise RuntimeError('Falha na ativação do Ponto de Acesso.')

        ip = wlan.ifconfig()[0]
        print(f'Ponto de Acesso "{self.ssid}" criado com sucesso.')
        print(f'Acesse o dashboard em: http://{ip}')
        return ip

    def open_socket(self, ip):
        address = (ip, 80)
        connection = socket.socket()
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connection.bind(address)
        connection.listen(5)
        return connection

    def web_page_dashboard(self):
        """Gera o HTML do dashboard com dados em tempo real."""
        temp_atual = self.thermal_controller.sensor.read()
        temp_alvo = self.thermal_controller.target
        freq_oscilacao_hz = self.frequency_sensor.frequency
        potencia = self.thermal_controller.actuator.read()

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

    def serve(self, connection):
        """Loop principal do servidor que aceita requisições e processa o formulário."""
        while True:
            client = None
            try:
                client = connection.accept()[0]
                request = client.recv(1024).decode()

                if request.split('\r\n')[0].startswith('GET /?target='):
                    try:
                        params = request.split('\r\n')[0].split('?')[
                            1].split('&')
                        for param in params:
                            if param.startswith('target='):
                                new_target = float(param.split('=')[1])
                                self.thermal_controller.set_target(new_target)
                                print(f"ALVO ATUALIZADO: {new_target:.1f}°C")
                                break
                    except Exception as e:
                        print(e)

                html = self.web_page_dashboard()

                client.send(
                    'HTTP/1.0 200 OK\r\nContent-type: text/html\r\nConnection: close\r\n\r\n')
                client.send(html)

            except OSError:
                # Erro de socket, fecha o cliente e continua
                pass
            except Exception as e:
                print(f'Erro inesperado no servidor: {e}')
                pass
            finally:
                if client:
                    client.close()


if __name__ == "__main__":
    from time import sleep
