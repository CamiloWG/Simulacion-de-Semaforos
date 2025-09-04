from dataclasses import dataclass


@dataclass
class Vehicle:
    id: int
    position: float  # distancia al stop line: >0 acercándose, 0 stop line, <0 más allá
    speed: float
    stopped: bool = False

    def step(self, new_position: float):
        self.position = new_position
