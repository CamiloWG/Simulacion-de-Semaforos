from .intersection import Intersection
from .lane import Lane


class Simulation:
    def __init__(self, intersection: Intersection, max_steps: int = 10000):
        self.intersection = intersection
        self.max_steps = max_steps
        self.time = 0
        self.next_vehicle_id = 1

    def step(self):
        self.time += 1
        vA = self.intersection.lane_A.spawn(self.next_vehicle_id)
        if vA:
            self.next_vehicle_id += 1
        vB = self.intersection.lane_B.spawn(self.next_vehicle_id)
        if vB:
            self.next_vehicle_id += 1

        self.intersection.lane_A.step_vehicles(
            light_green=(self.intersection.light_A.state == "green")
        )
        self.intersection.lane_B.step_vehicles(
            light_green=(self.intersection.light_B.state == "green")
        )

        self.intersection.step()

    def get_time(self):
        return self.time
