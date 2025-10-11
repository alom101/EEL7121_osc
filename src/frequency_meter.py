from machine import Timer, Pin


class FrequecyMeter:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN)
        self.pin.irq(handler=self.count_pulse_callback, trigger=Pin.IRQ_RISING)
        self.timer = Timer()
        self.timer.init(freq=1, callback=self.finish_callback)
        self.pulse_counter = 0
        self.freq = 0
        self.callbacks = []
        
    def set_callback(self, func):
        self.callbacks.append(func)
    
    def finish_callback(self, t):
        self.freq = self.pulse_counter
        self.pulse_counter = 0
        for cb in self.callbacks:
            cb(self)
        
    def count_pulse_callback(self, pin):
        self.pulse_counter += 1
        

if __name__=="__main__":
    from time import sleep
    def print_freq(fm):
        prinf(fm.freq)
        
    fm = FrequecyMeter(15)
    fm.set_callback(print_freq)
    
    while True:
        sleep(1)
        