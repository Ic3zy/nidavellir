import time


class ExecutionTimer:
    def __init__(self):
        self.start_time = time.perf_counter()
        self.temp_time = None

        self.current_watch = None

        self.timers = {}

    def start(self, name):
        if self.current_watch is not None:
            self.stop()

        self.current_watch = name
        self.temp_time = time.perf_counter()

    def stop(self):
        if self.current_watch is None:
            raise Exception("Not watching a timer")

        self.timers[self.current_watch] = time.perf_counter() - self.temp_time

        self.current_watch = None

    def print(self):
        if self.current_watch is not None:
            self.stop()

        for name, times in self.timers.items():
            print(f"{name}: {times:.3f} seconds")

        end_time = time.perf_counter()

        print(f"Total: {end_time-self.start_time:.3f} seconds")
