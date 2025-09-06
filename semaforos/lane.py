# semaforos/lane.py - Versión mejorada
from dataclasses import dataclass, field
from typing import List, Optional
import random
from .vehicle import Vehicle


@dataclass
class Lane:
    name: str
    vehicles: List[Vehicle] = field(default_factory=list)
    spawn_rate: float = 0.06
    max_speed: float = 1.0
    lane_length: float = 400.0
    min_gap_units: float = 6.0

    def step_vehicles(
        self, light_green: bool, stop_line: float = 0.0, stop_buffer: float = 0.0
    ):
        """
        Actualiza las posiciones de todos los vehículos con mejor manejo de separación.
        """
        if not self.vehicles:
            return

        # Separar vehículos en dos grupos: cruzando/saliendo vs aproximándose
        beyond = [v for v in self.vehicles if v.position < stop_line]
        approaching = [v for v in self.vehicles if v.position >= stop_line]

        # Procesar vehículos que ya cruzaron (mantener separación también aquí)
        if beyond:
            beyond.sort(key=lambda v: v.position, reverse=True)  # más lejos primero
            for i, v in enumerate(beyond):
                desired_pos = v.position - v.speed

                # Si hay un vehículo delante, mantener distancia
                if i > 0:
                    front_vehicle = beyond[i - 1]
                    min_allowed = front_vehicle.position + self.min_gap_units
                    if desired_pos < min_allowed:
                        desired_pos = min_allowed

                v.step(desired_pos)
                v.stopped = abs(desired_pos - v.position) < 0.01

        # Procesar vehículos que se acercan
        if approaching:
            approaching.sort(key=lambda v: v.position)  # más cerca primero

            stop_threshold = stop_line + (stop_buffer if not light_green else 0.0)

            for i, v in enumerate(approaching):
                current_pos = v.position
                desired_pos = current_pos - v.speed

                # Restricción 1: No pasar del semáforo en rojo
                if not light_green and desired_pos < stop_threshold:
                    desired_pos = stop_threshold

                # Restricción 2: No chocar con el vehículo de adelante
                if i > 0:
                    front_vehicle = approaching[i - 1]
                    min_allowed = front_vehicle.position + self.min_gap_units
                    if desired_pos < min_allowed:
                        desired_pos = min_allowed

                # Si el vehículo puede cruzar (luz verde y llegó al stop_line)
                elif light_green and desired_pos <= stop_line:
                    # Verificar que no haya vehículos muy cerca cruzando
                    can_cross = True
                    for other in beyond:
                        if abs(other.position) < self.min_gap_units:
                            can_cross = False
                            break

                    if not can_cross:
                        desired_pos = stop_line + 0.1  # esperar un poco

                v.step(desired_pos)
                v.stopped = abs(desired_pos - current_pos) < 0.01

        # Limpiar vehículos que salieron completamente
        self.vehicles = [v for v in self.vehicles if v.position > -self.lane_length]

    def spawn(self, next_vehicle_id: int) -> Optional[Vehicle]:
        """
        Genera un nuevo vehículo con probabilidad spawn_rate.
        Mejorado para evitar spawns cuando hay vehículos muy cerca del punto de spawn.
        """
        if random.random() > self.spawn_rate:
            return None

        # Verificar que no haya vehículos muy cerca del punto de spawn
        spawn_position = self.lane_length
        for v in self.vehicles:
            if v.position > spawn_position - self.min_gap_units * 2:
                return None  # No spawear si hay tráfico cerca

        # Variar ligeramente la velocidad para más realismo
        speed_variation = random.uniform(0.8, 1.2)
        actual_speed = self.max_speed * speed_variation

        vehicle = Vehicle(
            id=next_vehicle_id, position=spawn_position, speed=actual_speed
        )
        self.vehicles.append(vehicle)
        return vehicle

    def count_approaching_within(self, dist: float) -> int:
        """Cuenta vehículos que se acercan dentro de una distancia específica."""
        return sum(1 for v in self.vehicles if 0 < v.position <= dist)

    def count_within_r_to_cross(self, r: float) -> int:
        """Cuenta vehículos cerca de cruzar (dentro de distancia r del stop line)."""
        return sum(1 for v in self.vehicles if 0 < v.position <= r)

    def has_stopped_beyond_intersection_within(self, e: float) -> bool:
        """Verifica si hay vehículos detenidos justo después del cruce."""
        return any(
            v.position < 0 and abs(v.position) <= e and v.stopped for v in self.vehicles
        )

    def get_vehicle_count(self) -> int:
        """Retorna el número total de vehículos en el carril."""
        return len(self.vehicles)

    def get_waiting_vehicles(self) -> int:
        """Cuenta vehículos detenidos esperando el semáforo."""
        return sum(1 for v in self.vehicles if v.position > 0 and v.stopped)
