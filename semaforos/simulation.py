# semaforos/simulation.py - Simulación corregida
from .intersection import Intersection
import random


class Simulation:
    def __init__(self, intersection: Intersection, max_steps: int = 1000000):
        self.intersection = intersection
        self.max_steps = max_steps
        self.time = 0
        self.next_vehicle_id = 1

        # Estadísticas
        self.total_vehicles_spawned = 0
        self.total_vehicles_completed = 0

    def step(self):
        """Ejecuta un paso completo de la simulación."""
        if self.time >= self.max_steps:
            return False

        # 1) El cruce toma decisiones sobre los semáforos
        self.intersection.step()

        # 2) Mover vehículos según el estado actual de los semáforos
        la_green = self.intersection.light_A.state == "green"
        lb_green = self.intersection.light_B.state == "green"

        # Contar vehículos antes del movimiento
        vehicles_before_A = len(self.intersection.lane_A.vehicles)
        vehicles_before_B = len(self.intersection.lane_B.vehicles)

        # Mover vehículos (usando las líneas de parada correctas)
        self.intersection.lane_A.step_vehicles(
            light_green=la_green, stop_line=self.intersection.stop_line_A
        )
        self.intersection.lane_B.step_vehicles(
            light_green=lb_green, stop_line=self.intersection.stop_line_B
        )

        # Contar vehículos que completaron el recorrido
        vehicles_after_A = len(self.intersection.lane_A.vehicles)
        vehicles_after_B = len(self.intersection.lane_B.vehicles)

        completed = (vehicles_before_A - vehicles_after_A) + (
            vehicles_before_B - vehicles_after_B
        )
        self.total_vehicles_completed += max(0, completed)

        # 3) Generar nuevos vehículos
        self._spawn_vehicles()

        self.time += 1
        return True

    def _spawn_vehicles(self):
        """Genera nuevos vehículos en ambos carriles."""
        # Generar en carril A
        vehicle_A = self.intersection.lane_A.spawn(self.next_vehicle_id)
        if vehicle_A:
            self.next_vehicle_id += 1
            self.total_vehicles_spawned += 1

        # Generar en carril B
        vehicle_B = self.intersection.lane_B.spawn(self.next_vehicle_id)
        if vehicle_B:
            self.next_vehicle_id += 1
            self.total_vehicles_spawned += 1

    def get_time(self):
        """Retorna el tiempo actual."""
        return self.time

    def get_statistics(self):
        """Retorna estadísticas de la simulación."""
        state = self.intersection.get_state()
        efficiency = 0
        if self.total_vehicles_spawned > 0:
            efficiency = (
                self.total_vehicles_completed / self.total_vehicles_spawned
            ) * 100

        return {
            "time": self.time,
            "total_spawned": self.total_vehicles_spawned,
            "total_completed": self.total_vehicles_completed,
            "efficiency": efficiency,
            "intersection_state": state,
        }

    def reset(self):
        """Reinicia la simulación."""
        self.time = 0
        self.next_vehicle_id = 1
        self.total_vehicles_spawned = 0
        self.total_vehicles_completed = 0

        # Limpiar carriles
        self.intersection.lane_A.vehicles.clear()
        self.intersection.lane_B.vehicles.clear()

        # Reiniciar semáforos
        self.intersection.light_A.set_green()
        self.intersection.light_B.set_red()
        self.intersection.counter_A = 0
        self.intersection.counter_B = 0
        self.intersection.both_red = False
        self.intersection.both_red_timer = 0
        self.intersection.total_changes = 0
        self.intersection.last_change_reason = ""
