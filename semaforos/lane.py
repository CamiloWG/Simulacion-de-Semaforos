from dataclasses import dataclass, field
from typing import List, Optional
import random
import math
from .vehicle import Vehicle


@dataclass
class TrafficPattern:
    """Patrón de tráfico con variaciones dinámicas."""

    base_rate: float = 0.04
    peak_multiplier: float = 3.0
    low_multiplier: float = 0.3
    cycle_length: float = 300.0  # duración del ciclo completo
    peak_duration: float = 60.0  # duración de los picos
    current_time: float = 0.0
    phase_offset: float = 0.0  # desfase entre carriles


@dataclass
class Lane:
    name: str
    vehicles: List[Vehicle] = field(default_factory=list)
    traffic_pattern: TrafficPattern = field(default_factory=TrafficPattern)
    max_speed: float = 1.0
    lane_length: float = 400.0
    min_gap_units: float = 8.0
    vehicle_length: float = 5.0

    def __post_init__(self):
        if self.name == "A":
            self.traffic_pattern.phase_offset = random.uniform(
                0, 50
            )  # Inicio aleatorio
            self.traffic_pattern.base_rate = random.uniform(
                0.06, 0.10
            )  # Tasa base aleatoria
            self.traffic_pattern.peak_multiplier = random.uniform(2.0, 3.5)
            self.traffic_pattern.low_multiplier = random.uniform(0.3, 0.7)
            self.traffic_pattern.cycle_length = random.uniform(
                250, 350
            )  # Ciclos variables
        else:  # carril B
            self.traffic_pattern.phase_offset = random.uniform(
                100, 200
            )  # Diferente desfase
            self.traffic_pattern.base_rate = random.uniform(0.05, 0.09)
            self.traffic_pattern.peak_multiplier = random.uniform(2.2, 4.0)
            self.traffic_pattern.low_multiplier = random.uniform(0.2, 0.6)
            self.traffic_pattern.cycle_length = random.uniform(
                280, 380
            )  # Ciclo diferente

    def _calculate_current_spawn_rate(self) -> float:
        """Calcula la tasa de spawn actual basada en patrones de tráfico dinámicos."""
        pattern = self.traffic_pattern
        adjusted_time = (
            pattern.current_time + pattern.phase_offset
        ) % pattern.cycle_length

        # Crear múltiples picos durante el ciclo
        peak_1 = adjusted_time < pattern.peak_duration
        peak_2 = (
            (pattern.cycle_length * 0.4)
            < adjusted_time
            < (pattern.cycle_length * 0.4 + pattern.peak_duration)
        )
        low_period = (
            (pattern.cycle_length * 0.7) < adjusted_time < (pattern.cycle_length * 0.9)
        )

        # Añadir ruido aleatorio
        noise = random.uniform(0.8, 1.2)

        if peak_1 or peak_2:
            multiplier = pattern.peak_multiplier * noise
        elif low_period:
            multiplier = pattern.low_multiplier * noise
        else:
            multiplier = 1.0 * noise

        return pattern.base_rate * multiplier

    def step_vehicles(
        self, light_green: bool, stop_line: float = 0.0, stop_buffer: float = 0.5
    ):
        self.traffic_pattern.current_time += 1

        if not self.vehicles:
            return

        self.vehicles.sort(key=lambda v: v.position, reverse=True)

        # Procesar cada vehículo individualmente
        for i, vehicle in enumerate(self.vehicles):
            self._update_single_vehicle(vehicle, i, light_green, stop_line, stop_buffer)

        # Limpiar vehículos que salieron completamente del sistema
        self.vehicles = [v for v in self.vehicles if v.position > -self.lane_length]

    def _update_single_vehicle(
        self, vehicle, index, light_green, stop_line, stop_buffer
    ):
        # 1. Determinar velocidad objetivo basada en condiciones
        target_speed = self._calculate_target_speed(
            vehicle, index, light_green, stop_line, stop_buffer
        )

        # 2. Aplicar aceleración/desaceleración suave
        speed_change = target_speed - vehicle.speed
        max_acceleration = 0.4  # Aceleración máxima por step
        max_deceleration = 0.6  # Desaceleración máxima por step

        if speed_change > max_acceleration:
            vehicle.speed += max_acceleration
        elif speed_change < -max_deceleration:
            vehicle.speed -= max_deceleration
        else:
            vehicle.speed = target_speed

        # 3. Limitar velocidad dentro de rangos realistas
        vehicle.speed = max(0.0, min(self.max_speed * 1.2, vehicle.speed))

        # 4. Mover vehículo
        if vehicle.speed > 0.01:
            new_position = vehicle.position - vehicle.speed
            vehicle.step(new_position)
            vehicle.stopped = False
        else:
            vehicle.stopped = True

    def _calculate_target_speed(
        self, vehicle, index, light_green, stop_line, stop_buffer
    ):
        # Velocidad base con variación individual
        base_speed = self.max_speed * random.uniform(0.9, 1.1)
        target_speed = base_speed

        # Factor 1: Vehículo adelante
        front_vehicle = self._find_vehicle_ahead(vehicle)
        if front_vehicle:
            gap = front_vehicle.position - vehicle.position
            safe_gap = 0.8

            if gap < safe_gap * 1.5:  # Comenzar a reducir velocidad antes
                if gap < safe_gap:
                    target_speed = 0.0  # Detener si está muy cerca
                else:
                    # Reducir velocidad gradualmente según la distancia
                    gap_factor = (gap - safe_gap) / (safe_gap * 2)
                    target_speed *= max(0.2, gap_factor)

                # Si el vehículo de adelante está parado, parar también
                if front_vehicle.stopped and gap < safe_gap * 1.5:
                    target_speed = 0.0

        # Factor 2: Semáforo (solo afecta si no hay vehículo adelante muy cerca)
        if (
            not front_vehicle
            or (front_vehicle.position - vehicle.position) > self.min_gap_units * 2
        ):
            distance_to_stop = vehicle.position - stop_line

            if not light_green and distance_to_stop > 0:
                # Zona de desaceleración más amplia y suave
                deceleration_zone = 80.0  # Distancia para comenzar a frenar

                if distance_to_stop < deceleration_zone:
                    if distance_to_stop < stop_buffer + 1.0:
                        target_speed = 0.0  # Parar en la línea
                    else:
                        # Desaceleración suave y progresiva
                        slow_factor = (
                            distance_to_stop - stop_buffer
                        ) / deceleration_zone
                        target_speed *= max(0.1, slow_factor)

        return target_speed

    def _find_vehicle_ahead(self, current_vehicle):
        closest_vehicle = None
        min_distance = float("inf")

        for other_vehicle in self.vehicles:
            if (
                other_vehicle.id != current_vehicle.id
                and other_vehicle.position < current_vehicle.position
            ):

                distance = current_vehicle.position - other_vehicle.position
                if (
                    distance < min_distance and distance < 150
                ):  # Solo considerar vehículos cercanos
                    min_distance = distance
                    closest_vehicle = other_vehicle

        return closest_vehicle

    def spawn(self, next_vehicle_id: int) -> Optional[Vehicle]:
        current_rate = self._calculate_current_spawn_rate()

        if random.random() > current_rate:
            return None

        # Verificar espacio disponible
        spawn_position = self.lane_length
        min_spawn_gap = 0.5

        # Solo verificar vehículos muy cerca del punto de spawn
        for v in self.vehicles:
            if v.position > spawn_position - min_spawn_gap:
                return None  # No hay espacio suficiente

        # Crear vehículo
        speed_variation = random.uniform(0.8, 1.3)
        actual_speed = self.max_speed * speed_variation

        vehicle = Vehicle(
            id=next_vehicle_id, position=spawn_position, speed=actual_speed
        )
        self.vehicles.append(vehicle)
        return vehicle

    def count_approaching_within(self, dist: float) -> int:
        """Cuenta vehículos que se acercan dentro de una distancia específica del stop line."""
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

    def get_traffic_info(self) -> dict:
        current_rate = self._calculate_current_spawn_rate()

        # Calcular separaciones promedio entre vehículos
        separations = []
        sorted_vehicles = sorted(self.vehicles, key=lambda v: v.position, reverse=True)
        for i in range(len(sorted_vehicles) - 1):
            sep = sorted_vehicles[i].position - sorted_vehicles[i + 1].position
            separations.append(sep)

        avg_separation = sum(separations) / len(separations) if separations else 0
        min_separation = min(separations) if separations else 0

        return {
            "current_spawn_rate": current_rate,
            "traffic_time": self.traffic_pattern.current_time,
            "approaching_vehicles": self.count_approaching_within(150),
            "waiting_vehicles": self.get_waiting_vehicles(),
            "total_vehicles": len(self.vehicles),
            "avg_separation": avg_separation,
            "min_separation": min_separation,
            "stopped_vehicles": sum(1 for v in self.vehicles if v.stopped),
            "moving_vehicles": sum(1 for v in self.vehicles if not v.stopped),
            "spawn_rate_category": self._get_traffic_category(current_rate),
            "cycle_progress": (
                self.traffic_pattern.current_time % self.traffic_pattern.cycle_length
            )
            / self.traffic_pattern.cycle_length
            * 100,
        }

    def _get_traffic_category(self, rate: float) -> str:
        if rate == 0:
            return "SIN TRÁFICO"
        elif rate < 0.02:
            return "MUY BAJO"
        elif rate < 0.05:
            return "BAJO"
        elif rate < 0.10:
            return "MODERADO"
        elif rate < 0.15:
            return "ALTO"
        else:
            return "PICO MÁXIMO"
