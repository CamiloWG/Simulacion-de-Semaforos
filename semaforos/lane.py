# semaforos/lane.py - Sistema de flujo de tráfico completamente renovado
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
        # Configurar patrones diferentes para cada carril
        if self.name == "A":
            self.traffic_pattern.phase_offset = 0.0
            self.traffic_pattern.base_rate = 0.045
        else:  # carril B
            self.traffic_pattern.phase_offset = 150.0  # desfasado
            self.traffic_pattern.base_rate = 0.035

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
        """
        Sistema de movimiento de vehículos completamente renovado.
        """
        self.traffic_pattern.current_time += 1

        if not self.vehicles:
            return

        # Actualizar velocidades basadas en condiciones locales
        self._update_vehicle_speeds(light_green, stop_line, stop_buffer)

        # Mover vehículos con nueva lógica
        self._move_vehicles_improved()

        # Limpiar vehículos que salieron
        self.vehicles = [v for v in self.vehicles if v.position > -self.lane_length]

    def _update_vehicle_speeds(
        self, light_green: bool, stop_line: float, stop_buffer: float
    ):
        """Actualiza las velocidades de los vehículos basándose en las condiciones."""
        if not self.vehicles:
            return

        # Ordenar por posición (más cerca del stop line primero)
        self.vehicles.sort(key=lambda v: v.position)

        for i, vehicle in enumerate(self.vehicles):
            # Velocidad base
            target_speed = self.max_speed * random.uniform(0.85, 1.05)

            # Factor 1: Semáforo rojo
            distance_to_stop = vehicle.position - stop_line
            if not light_green and distance_to_stop > 0:
                # Reducir velocidad gradualmente al acercarse al semáforo rojo
                if distance_to_stop < 50:
                    slow_factor = max(0.1, distance_to_stop / 50.0)
                    target_speed *= slow_factor

                # Detener completamente cerca del stop line
                if distance_to_stop < stop_buffer + 2.0:
                    target_speed = 0.0

            # Factor 2: Vehículo adelante
            if i > 0:  # Hay un vehículo adelante
                front_vehicle = self.vehicles[i - 1]
                gap = front_vehicle.position - vehicle.position
                safe_gap = self.min_gap_units + self.vehicle_length

                if gap < safe_gap * 2:  # Si está demasiado cerca
                    # Ajustar velocidad para mantener distancia segura
                    gap_factor = max(0.0, gap / (safe_gap * 2))
                    target_speed *= gap_factor

                    # Si el vehículo de adelante está parado
                    if front_vehicle.stopped:
                        target_speed = 0.0

            # Factor 3: Aceleración/desaceleración suave
            speed_diff = target_speed - vehicle.speed
            max_acceleration = 0.3

            if abs(speed_diff) > max_acceleration:
                if speed_diff > 0:
                    vehicle.speed += max_acceleration
                else:
                    vehicle.speed -= max_acceleration
            else:
                vehicle.speed = target_speed

            # Limitar velocidad
            vehicle.speed = max(0.0, min(self.max_speed * 1.1, vehicle.speed))

    def _move_vehicles_improved(self):
        """Mueve los vehículos con lógica mejorada."""
        for vehicle in self.vehicles:
            if vehicle.speed > 0.01:
                new_position = vehicle.position - vehicle.speed
                vehicle.step(new_position)
                vehicle.stopped = False
            else:
                vehicle.stopped = True

    def spawn(self, next_vehicle_id: int) -> Optional[Vehicle]:
        """
        Genera nuevos vehículos con patrones de tráfico dinámicos.
        """
        current_rate = self._calculate_current_spawn_rate()

        if random.random() > current_rate:
            return None

        # Verificar espacio disponible
        spawn_position = self.lane_length
        min_spawn_gap = self.min_gap_units * 3

        for v in self.vehicles:
            if v.position > spawn_position - min_spawn_gap:
                return None  # No hay espacio suficiente

        # Crear vehículo con características variadas
        speed_variation = random.uniform(0.8, 1.2)
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
        """Retorna información sobre el estado del tráfico."""
        return {
            "current_spawn_rate": self._calculate_current_spawn_rate(),
            "traffic_time": self.traffic_pattern.current_time,
            "approaching_vehicles": self.count_approaching_within(150),
            "waiting_vehicles": self.get_waiting_vehicles(),
            "total_vehicles": len(self.vehicles),
        }
