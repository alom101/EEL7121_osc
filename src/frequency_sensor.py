from machine import Timer, Pin
from time import ticks_us
from rp2 import asm_pio, StateMachine
from data_history import DataHistory

class FreqSensorInterface:
    @property
    def frequency(self):
        raise NotImplementedError()


@asm_pio()
def pio_code():
    wrap_target()
    mov(x, y)
    label("count")
    wait(1, pin, 0)
    wait(0, pin, 0)
    jmp(x_dec, "count")
    irq(rel(0))
    wrap()



class FreqSensorPIO(FreqSensorInterface):
    def __init__(self, pin, count_to=500_000, sm_id=0, sm_freq=125_000_000, history_size=40):
        # adicionar no init -> history_size=40
        self.last_measured_freq = 0
        self.last_interrupt = ticks_us()
        self.count_to = count_to
        self.count_to_scaled = self.count_to*1e6
        self.pin = Pin(pin, Pin.IN)
        self.state_machine = StateMachine(sm_id, pio_code, freq=sm_freq, in_base=self.pin)
        self.init_state_machine()
        self.freq_history = DataHistory(history_size)

    def init_state_machine(self):
        self.state_machine.irq(self.new_measure_callback)
        self.state_machine.put(self.count_to)
        self.state_machine.exec("pull()")
        self.state_machine.exec("mov(y, osr)")
        self.state_machine.active(1)

    def new_measure_callback(self, pio):
        interrupt_time = ticks_us()
        delta = interrupt_time - self.last_interrupt
        self.last_measured_freq = self.count_to_scaled/delta
        self.last_interrupt = interrupt_time
        #self.freq_history.add_point(self.last_measured_freq)
        
        #print(f"New frequency value: {self.frequency}, delta={delta}, count:{self.count_to}")
        #print(f"New frequency value: {self.frequency}")

    @property
    def frequency(self):
        return self.last_measured_freq




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

    from tests import Clock
    clk = Clock(pin=14, freq=455_000)
    
    # fm = FreqSensorPulseCounter(15, measure_freq=1.0)
    fm = FreqSensorPIO(15, count_to=100_000)

    try:
        while True:
            sleep(0.2)
            desvio = fm.frequency-500
            #print(f"{(fm.frequency-500)*1000} mHz")
            print(fm.frequency)
    except KeyboardInterrupt:
        fm.state_machine.active(0)
        print("SM stopped")
        
    print('code ended')
