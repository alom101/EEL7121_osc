class DataHistory:
    
    def __init__(self, max_size=40):
        self.max_size = max_size
        self.history = []

    def add_point(self, value): 
        self.history.append(value)
        if len(self.history) > self.max_size:
            self.history.pop(0)

    def get_data(self):
        return list(self.history)

    def get_last_data(self):
        return self.history[-1]

    def get_variation(self):
        return self.history[-1] - self.history[-2]
