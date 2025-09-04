from dataclasses import dataclass, field
from typing import List, Optional
import random
from .vehicle import Vehicle


@dataclass
class Lane:
    name: str
    vehicles: List[Vehicle] = field(default_factory=list)
    spawn_rate: float = 0.2
    max_speed: float = 1.0
    lane_length: float = 200.0

    def step_vehicles(self, light_green: bool, stop_line: float = 0.0):
        self.vehicles.sort(key=lambda v: -v.position)
        next_positions = {}
        for i, v in enumerate(self.vehicles):
            if v.position < 0:
                new_pos = v.position - v.speed
                v.stopped = False
                next_positions[v.id] = new_pos
                continue

            dist_to_front = float("inf")
            if i != 0:
                front = self.vehicles[i - 1]
                dist_to_front = front.position - v.position

            desired_pos = v.position - v.speed
            if dist_to_front is not None and dist_to_front <= 1.0:
                new_pos = v.position
                v.stopped = True
            else:
                if desired_pos <= stop_line:
                    if light_green:
                        new_pos = desired_pos
                        v.stopped = False
                    else:
                        new_pos = max(stop_line, v.position)
                        v.stopped = True
                else:
                    new_pos = desired_pos
                    v.stopped = False

            next_positions[v.id] = new_pos

        for v in self.vehicles:
            v.step(next_positions[v.id])

        self.vehicles = [v for v in self.vehicles if v.position > -self.lane_length]

    def spawn(self, next_vehicle_id: int) -> Optional[Vehicle]:
        if random.random() < self.spawn_rate:
            v = Vehicle(
                id=next_vehicle_id, position=self.lane_length, speed=self.max_speed
            )
            self.vehicles.append(v)
            return v
        return None

    def count_approaching_within(self, dist: float) -> int:
        return sum(1 for v in self.vehicles if 0 < v.position <= dist)

    def count_within_r_to_cross(self, r: float) -> int:
        return sum(1 for v in self.vehicles if 0 < v.position <= r)

    def has_stopped_beyond_intersection_within(self, e: float) -> bool:
        return any(
            v.position < 0 and abs(v.position) <= e and v.stopped for v in self.vehicles
        )
