

class StrategyInterface:
    def update(self, current_value, target):
        raise NotImplementedError()


class StrategyOnOff(StrategyInterface):
    def update(self, current_value, target):
        if current_value < target:
            return 2**16
        return 0


class StrategyP(StrategyInterface):
    def __init__(self, Kp=10):
        self.Kp = Kp
    def update(self, current_value, target):
        error = target - current_value
        P = error*self.Kp
        return max(min(P,2**16), 0)
#
#
# class StrategyPI(StrategyInterface):
#     def __init__(self, Kp=10, Ki=0.1):
#         self.Kp = Kp
#         self.Ki = Ki
#         self.integral = 0
#
#     def update(self, current_value, target):
#         error = target - current_value
#         P = error*self.Kp
#         self.integral += error*self.Ki
#         output = P + self.integral
#         return max(min(output,2**16), 0)
