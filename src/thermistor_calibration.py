from temperature_sensor import SensorDS18B20, SensorThermistorRseries
from time import sleep, gmtime

PERIOD = 1 # seconds

sensor_reference = SensorDS18B20(4)
sensor_thermistor= SensorThermistorRseries(27, 10_000, 1,1)

with open("calibration_data.tsv", "wt") as file:
    file.write("time\ttemperature\tresistance\n")
    while True:
        t = gmtime()
        T = sensor_reference.read()
        R = sensor_thermistor.temperature_to_resistance(sensor_thermistor.read())
        str = f"{t}\t{T}\t{R}\n"
        file.write(str)
        print(str, end='')
        sleep(PERIOD)
