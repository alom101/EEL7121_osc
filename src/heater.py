from machine import Pin

class Heater:
    def __init__(self, pin):
        self.pin = Pin(pin)

    def status(self):
        return self.pin()

    def on(self):
        self.pin.on()

    def off(self):
        self.pin.off()

