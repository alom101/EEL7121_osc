from machine import Timer, Pin


class FreqSensorInterface:
    @property
    def frequency(self):
        raise NotImplementedError()


class FreqSensorPulseCounter(FreqSensorInterface):
    def __init__(self, pin, measure_freq=1):
        self.pin = Pin(pin, Pin.IN)
        self.pin.irq(handler=self.count_pulse_callback, trigger=Pin.IRQ_RISING)
        self.timer = Timer()
        self.measure_freq = measure_freq
        self.timer.init(freq=measure_freq, callback=self.finish_callback)
        self.pulse_counter = 0
        self.freq = 0
        self.callbacks = []
        
    @property
    def frequency(self):
        return self.freq

    def set_callback(self, func):
        self.callbacks.append(func)

    def finish_callback(self, t):
        self.freq = self.pulse_counter*self.measure_freq
        self.pulse_counter = 0
        for cb in self.callbacks:
            cb(self)

    def count_pulse_callback(self, pin):
        self.pulse_counter += 1


if __name__ == "__main__":
    from time import sleep

    def print_freq(fm):
        print(fm.frequency)
        

    out = Pin(14, Pin.OUT) # para simular um oscilador
    toggle = out.toggle
    def toogle_output(t):
        toggle()
    out_timer = Timer()
    freq = 1234
    out_timer.init(freq=freq*2, callback=toogle_output)
    
    fm = FreqSensorPulseCounter(15, measure_freq=1.0)
    fm.set_callback(print_freq)

    toggle = out.toggle
    while True:
        sleep(1)