from temperature_sensor import SensorDS18B20, SensorThermistorRseries
from time import sleep, time
from machine import Pin
from os import listdir

PERIOD = 1  # seconds
BASE_NAME = "calibration_data_"

sensor_reference = SensorDS18B20(4)
sensor_thermistor = SensorThermistorRseries(27, 10_000, 1, 1)
led_builtin = Pin(25, Pin.OUT)


# get new file_name
i = 1
file_name = BASE_NAME + str(i) + ".tsv"
while file_name in listdir():
    i += 1
    file_name = BASE_NAME + str(i) + ".tsv"
print(f"Writing to {file_name}")

# set header
header = "time\ttemperature\tresistance\n"
with open(file_name, "at") as file:
    file.write(header)
print(header, end='')

# wait SensorDS18B20 setup time
while sensor_reference.read() == 0:
    sleep(0.1)

# begin recording
t0 = time()
while True:
    led_builtin.on()
    t = time()-t0
    T = sensor_reference.read()
    R = sensor_thermistor.temperature_to_resistance(
            sensor_thermistor.read()
        )
    str = f"{t}\t{T}\t{R}\n"
    with open(file_name, "at") as file:
        file.write(str)
    print(str, end='')
    led_builtin.off()
    sleep(PERIOD)
