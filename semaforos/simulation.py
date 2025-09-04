from .intersection import Intersection


class Simulation:
    def __init__(self, intersection: Intersection, max_steps: int = 1000000):
        self.intersection = intersection
        self.max_steps = max_steps
        self.time = 0
        self.next_vehicle_id = 1

    def step(self):
        # 1) intersection.step first (decides if a light should change)
        self.intersection.step()

        # 2) move existing vehicles based on the new light state
        la_green = self.intersection.light_A.state == "green"
        lb_green = self.intersection.light_B.state == "green"
        self.intersection.lane_A.step_vehicles(
            light_green=la_green, stop_line=0.0, stop_buffer=self.intersection.r
        )
        self.intersection.lane_B.step_vehicles(
            light_green=lb_green, stop_line=0.0, stop_buffer=self.intersection.r
        )

        # 3) spawn new vehicles
        vA = self.intersection.lane_A.spawn(self.next_vehicle_id)
        if vA:
            self.next_vehicle_id += 1
        vB = self.intersection.lane_B.spawn(self.next_vehicle_id)
        if vB:
            self.next_vehicle_id += 1

        self.time += 1

    def get_time(self):
        return self.time
