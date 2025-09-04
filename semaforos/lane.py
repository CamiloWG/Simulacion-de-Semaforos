# semaforos/lane.py
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
    lane_length: float = 350.0
    min_gap_units: float = 4.0

    def step_vehicles(
        self, light_green: bool, stop_line: float = 0.0, stop_buffer: float = 0.0
    ):
        next_positions = {}

        # 1) Vehicles that have already crossed (position < 0) -> keep moving away
        beyond = [v for v in self.vehicles if v.position < 0]
        for v in beyond:
            v.step(v.position - v.speed)
            v.stopped = False
            next_positions[v.id] = v.position

        # 2) Approaching vehicles (position >= 0)
        approach = [v for v in self.vehicles if v.position >= 0]
        approach.sort(key=lambda v: v.position)

        for i, v in enumerate(approach):
            current_pos = v.position

            # Start with the desired position based on speed
            desired_pos = current_pos - v.speed
            new_pos = desired_pos

            # Constraint 1: Stop behind the car in front
            if i > 0:
                front = approach[i - 1]
                front_pos_after_move = next_positions.get(front.id, front.position)
                min_allowed_pos = front_pos_after_move + self.min_gap_units
                if new_pos < min_allowed_pos:
                    new_pos = min_allowed_pos

            # Constraint 2: Stop at the traffic light if red
            if not light_green:
                stop_threshold = stop_line + stop_buffer
                if new_pos < stop_threshold:
                    new_pos = stop_threshold

            # Check if the vehicle is stopped
            v.stopped = abs(new_pos - current_pos) < 0.01

            # Apply the new position
            v.step(new_pos)
            next_positions[v.id] = new_pos

        # Clean up vehicles that have left the screen completely
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
