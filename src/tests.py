from time import ticks_us

def execution_time(func, *args, **kwargs):
    t0 = ticks_us()
    func(*args, **kwargs)
    t1 = ticks_us()
    return (t1-t0)/1e6

def profile(profiles):
    print(f'{"Name":^30}\t{"exec time (ms)":^15}\t{"max freq (Hz)":^15}')
    for prof in profiles:
        func_name = prof['func_name']
        func = prof['func']
        args = prof['args'] if 'args' in prof else ()
        kwargs = prof['kwargs'] if 'kwargs' in prof else {}

        exec_time = execution_time(func, *args, **kwargs)
        print(f'{func_name:^30}\t{exec_time*1000:^15}\t{1/exec_time:^15.0f}''')

