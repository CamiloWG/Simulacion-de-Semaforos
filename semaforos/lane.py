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
    lane_length: float = 350.0  # distancia de spawn / hasta fuera de pantalla
    min_gap_units: float = 4.0  # separación física mínima (unidades del modelo)

    def step_vehicles(
        self, light_green: bool, stop_line: float = 0.0, stop_buffer: float = 0.0
    ):
        """
        Actualiza posiciones de vehículos:
        - Procesamos vehículos en aproximación (position >= 0) desde el más cercano al stop line hacia atrás
          para respetar separación física.
        - Los vehículos con position < 0 (ya cruzaron) siguen avanzando.
        - stop_buffer: distancia adicional (unidades) donde los vehículos se detienen antes de la línea si la luz está roja.
        """
        next_positions = {}

        # 1) Vehículos que ya cruzaron (position < 0) -> siguen alejándose
        beyond = [v for v in self.vehicles if v.position < 0]
        for v in beyond:
            new_pos = v.position - v.speed
            v.stopped = False
            next_positions[v.id] = new_pos

        # 2) Vehículos en aproximación (position >= 0)
        # ordenar por posición ASC (menor posición = más cercano al stop line)
        approach = [v for v in self.vehicles if v.position >= 0]
        approach.sort(key=lambda v: v.position)

        for i, v in enumerate(approach):
            current_pos = v.position
            desired_pos = current_pos - v.speed  # intentar avanzar hacia 0

            # Si semáforo rojo (o amarillo), no puede pasar del punto de parada (stop_line + stop_buffer)
            stop_threshold = stop_line + (stop_buffer if not light_green else 0.0)
            if (not light_green) and desired_pos <= stop_threshold:
                tentative_pos = max(stop_threshold, current_pos)
            else:
                tentative_pos = desired_pos

            # Si hay vehículo delante (ya procesado), respetar separación física min_gap_units
            if i > 0:
                front = approach[i - 1]
                front_new = next_positions.get(front.id, front.position)
                min_allowed = front_new + self.min_gap_units
                if tentative_pos < min_allowed:
                    # frena y mantiene su posición actual (no retrocede)
                    new_pos = current_pos
                    v.stopped = True
                else:
                    new_pos = tentative_pos
                    v.stopped = False
            else:
                # sin vehículo delante
                new_pos = tentative_pos
                v.stopped = not light_green and new_pos <= stop_threshold

            next_positions[v.id] = new_pos

        # aplicar nuevas posiciones
        for v in self.vehicles:
            if v.id in next_positions:
                v.step(next_positions[v.id])

        # limpiar vehículos que ya salieron totalmente (más allá de -lane_length)
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
