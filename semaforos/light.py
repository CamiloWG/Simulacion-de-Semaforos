# semaforos/light.py
from dataclasses import dataclass


@dataclass
class TrafficLight:
    name: str
    state: str = "red"
    green_time: int = 0

    def set_green(self):
        self.state = "green"
        self.green_time = 0

    def set_red(self):
        self.state = "red"
        self.green_time = 0

    def step_time(self):
        if self.state == "green":
            self.green_time += 1
