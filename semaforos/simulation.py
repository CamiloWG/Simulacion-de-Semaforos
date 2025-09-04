from .intersection import Intersection


class Simulation:
    def __init__(self, intersection: Intersection, max_steps: int = 1000000):
        self.intersection = intersection
        self.max_steps = max_steps
        self.time = 0
        self.next_vehicle_id = 1

    def step(self):
        # 1) intersection.step primero (decide si pone amarillo / completa cambios)
        self.intersection.step()

        # 2) spawn nuevos vehículos (aparecen lejos y se moverán en step_vehicles)
        vA = self.intersection.lane_A.spawn(self.next_vehicle_id)
        if vA:
            self.next_vehicle_id += 1
        vB = self.intersection.lane_B.spawn(self.next_vehicle_id)
        if vB:
            self.next_vehicle_id += 1

        # 3) mover vehículos respetando el estado actual de las luces
        # paso: los vehículos se detienen en stop_buffer = r de la intersección cuando luz != green
        la_green = self.intersection.light_A.state == "green"
        lb_green = self.intersection.light_B.state == "green"
        self.intersection.lane_A.step_vehicles(
            light_green=la_green, stop_line=0.0, stop_buffer=self.intersection.r
        )
        self.intersection.lane_B.step_vehicles(
            light_green=lb_green, stop_line=0.0, stop_buffer=self.intersection.r
        )

        self.time += 1

    def get_time(self):
        return self.time
