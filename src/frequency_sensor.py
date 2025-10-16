from machine import Timer, Pin
from rp2 import asm_pio, PIO, StateMachine


class FreqSensorInterface:
    @property
    def frequency(self):
        raise NotImplementedError()


class FreqSensorPIO(FreqSensorInterface):
    def __init__(self, expected_freq=400_000):
        self.expected_freq = expected_freq
        self.last_frequency = 0
        self.count_to = expected_freq #change later
        self.state_machine = StateMachine(0, self.pio_code, freq=1_000_000)
        self.init_state_machine()

    def init_state_machine(self):
        self.state_machine.irq(self.new_measure_callback)
        self.state_machine.put(self.count_to)
        self.state_machine.exec("pull()")
        self.state_machine.exec("mov(osr,y)")
        self.state_machine.active(True)
    
    @asm_pio()
    def pio_code(self):
        wrap_target()
        mov


        wrap()

    def new_measure_callback(self):
    # get value from state_machine
    # save on self.last_frequency



    @property
    def frequency(self):
        return self.last_frequency




class FreqSensorPulseCounter(FreqSensorInterface):
    def __init__(self, pin, measure_freq=1):
        self.pin = Pin(pin, Pin.IN)
        self.pin.irq(handler=self.count_pulse_callback, trigger=Pin.IRQ_RISING)
        self.timer = Timer()
        self.measure_freq = measure_freq
        self.timer.init(freq=measure_freq, callback=self.finish_callback, hard=False)
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

    out = Pin(14, Pin.OUT) # para simular um oscilador
    toggle = out.toggle
    def toogle_output(t):
        toggle()
    out_timer = Timer()
    freq = 10000
    out_timer.init(freq=freq*2, callback=toogle_output)
    
    # fm = FreqSensorPulseCounter(15, measure_freq=1.0)
    fm = FreqSensorPIO()

    toggle = out.toggle
    while True:
        print(fm.freq)
        sleep(1)
