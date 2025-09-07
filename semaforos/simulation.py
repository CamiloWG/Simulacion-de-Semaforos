from .intersection import Intersection
import random


class Simulation:
    def __init__(self, intersection: Intersection, max_steps: int = 1000000):
        self.intersection = intersection
        self.max_steps = max_steps
        self.time = 0
        self.next_vehicle_id = 1

        # Estadísticas mejoradas
        self.total_vehicles_spawned = 0
        self.total_vehicles_completed = 0
        self.total_waiting_time = 0  # Tiempo total de espera acumulado
        self.vehicles_wait_history = []  # Historial de tiempos de espera
        self.throughput_history = []  # Historial de rendimiento

        # Métricas por carril
        self.lane_A_spawned = 0
        self.lane_A_completed = 0
        self.lane_B_spawned = 0
        self.lane_B_completed = 0

        # Métricas de eficiencia
        self.avg_wait_time = 0.0
        self.system_efficiency = 0.0

    def step(self):
        """Ejecuta un paso completo de la simulación."""
        if self.time >= self.max_steps:
            return False

        # 1) El cruce toma decisiones sobre los semáforos
        self.intersection.step()

        # 2) Obtener estado de los semáforos
        la_green = self.intersection.light_A.state == "green"
        lb_green = self.intersection.light_B.state == "green"

        # 3) Contar vehículos antes del movimiento para métricas
        vehicles_before_A = len(self.intersection.lane_A.vehicles)
        vehicles_before_B = len(self.intersection.lane_B.vehicles)

        # 4) Actualizar tiempo de espera acumulado
        self._update_waiting_metrics()

        # 5) Mover vehículos
        self.intersection.lane_A.step_vehicles(
            light_green=la_green,
            stop_line=self.intersection.stop_line_A,
            stop_buffer=2.0,  # Buffer más realista
        )
        self.intersection.lane_B.step_vehicles(
            light_green=lb_green,
            stop_line=self.intersection.stop_line_B,
            stop_buffer=2.0,
        )

        # 6) Contar vehículos completados
        vehicles_after_A = len(self.intersection.lane_A.vehicles)
        vehicles_after_B = len(self.intersection.lane_B.vehicles)

        completed_A = max(0, vehicles_before_A - vehicles_after_A)
        completed_B = max(0, vehicles_before_B - vehicles_after_B)

        self.lane_A_completed += completed_A
        self.lane_B_completed += completed_B
        self.total_vehicles_completed += completed_A + completed_B

        # 7) Generar nuevos vehículos
        self._spawn_vehicles()

        # 8) Actualizar métricas cada 100 steps
        if self.time % 100 == 0:
            self._update_efficiency_metrics()

        self.time += 1
        return True

    def _update_waiting_metrics(self):
        """Actualiza métricas de tiempo de espera."""
        # Sumar tiempo de espera de todos los vehículos detenidos
        waiting_A = self.intersection.lane_A.get_waiting_vehicles()
        waiting_B = self.intersection.lane_B.get_waiting_vehicles()

        self.total_waiting_time += waiting_A + waiting_B

    def _update_efficiency_metrics(self):
        """Actualiza métricas de eficiencia del sistema."""
        if self.total_vehicles_spawned > 0:
            self.system_efficiency = (
                self.total_vehicles_completed / self.total_vehicles_spawned
            ) * 100

        if self.time > 0:
            self.avg_wait_time = self.total_waiting_time / max(1, self.time)

        # Guardar en historial
        current_throughput = self.total_vehicles_completed / max(1, self.time / 100.0)
        self.throughput_history.append(current_throughput)

        # Mantener solo los últimos 50 registros
        if len(self.throughput_history) > 50:
            self.throughput_history.pop(0)

    def _spawn_vehicles(self):
        """Genera nuevos vehículos en ambos carriles."""
        # Generar en carril A
        vehicle_A = self.intersection.lane_A.spawn(self.next_vehicle_id)
        if vehicle_A:
            self.next_vehicle_id += 1
            self.total_vehicles_spawned += 1
            self.lane_A_spawned += 1

        # Generar en carril B
        vehicle_B = self.intersection.lane_B.spawn(self.next_vehicle_id)
        if vehicle_B:
            self.next_vehicle_id += 1
            self.total_vehicles_spawned += 1
            self.lane_B_spawned += 1

    def get_time(self):
        """Retorna el tiempo actual."""
        return self.time

    def get_statistics(self):
        """Retorna estadísticas completas de la simulación."""
        state = self.intersection.get_state()

        # Eficiencias por carril
        efficiency_A = 0
        efficiency_B = 0
        if self.lane_A_spawned > 0:
            efficiency_A = (self.lane_A_completed / self.lane_A_spawned) * 100
        if self.lane_B_spawned > 0:
            efficiency_B = (self.lane_B_completed / self.lane_B_spawned) * 100

        # Obtener información de tráfico de cada carril
        traffic_A = self.intersection.lane_A.get_traffic_info()
        traffic_B = self.intersection.lane_B.get_traffic_info()

        return {
            "time": self.time,
            "total_spawned": self.total_vehicles_spawned,
            "total_completed": self.total_vehicles_completed,
            "system_efficiency": self.system_efficiency,
            "avg_wait_time": self.avg_wait_time,
            "intersection_state": state,
            # Estadísticas por carril
            "lane_A": {
                "spawned": self.lane_A_spawned,
                "completed": self.lane_A_completed,
                "efficiency": efficiency_A,
                "traffic_info": traffic_A,
            },
            "lane_B": {
                "spawned": self.lane_B_spawned,
                "completed": self.lane_B_completed,
                "efficiency": efficiency_B,
                "traffic_info": traffic_B,
            },
            # Métricas de rendimiento
            "throughput_history": self.throughput_history[-10:],  # Últimos 10
            "current_throughput": (
                self.throughput_history[-1] if self.throughput_history else 0
            ),
        }

    def reset(self):
        """Reinicia la simulación."""
        self.time = 0
        self.next_vehicle_id = 1
        self.total_vehicles_spawned = 0
        self.total_vehicles_completed = 0
        self.total_waiting_time = 0
        self.vehicles_wait_history.clear()
        self.throughput_history.clear()

        # Reiniciar métricas por carril
        self.lane_A_spawned = 0
        self.lane_A_completed = 0
        self.lane_B_spawned = 0
        self.lane_B_completed = 0

        self.avg_wait_time = 0.0
        self.system_efficiency = 0.0

        # Limpiar carriles
        self.intersection.lane_A.vehicles.clear()
        self.intersection.lane_B.vehicles.clear()

        # Reiniciar patrones de tráfico
        self.intersection.lane_A.traffic_pattern.current_time = 0.0
        self.intersection.lane_B.traffic_pattern.current_time = 0.0

        # Reiniciar semáforos
        self.intersection.light_A.set_green()
        self.intersection.light_B.set_red()
        self.intersection.counter_A = 0
        self.intersection.counter_B = 0
        self.intersection.both_red = False
        self.intersection.both_red_timer = 0
        self.intersection.total_changes = 0
        self.intersection.last_change_reason = ""

    def get_debug_info(self):
        """Retorna información de depuración detallada."""
        return {
            "rule_checks": {
                "vehicles_approaching_A": self.intersection.lane_A.count_approaching_within(
                    self.intersection.d
                ),
                "vehicles_approaching_B": self.intersection.lane_B.count_approaching_within(
                    self.intersection.d
                ),
                "vehicles_close_A": self.intersection.lane_A.count_within_r_to_cross(
                    self.intersection.r
                ),
                "vehicles_close_B": self.intersection.lane_B.count_within_r_to_cross(
                    self.intersection.r
                ),
                "blocked_after_A": self.intersection.lane_A.has_stopped_beyond_intersection_within(
                    self.intersection.e
                ),
                "blocked_after_B": self.intersection.lane_B.has_stopped_beyond_intersection_within(
                    self.intersection.e
                ),
                "counter_A": self.intersection.counter_A,
                "counter_B": self.intersection.counter_B,
                "light_A_green_time": self.intersection.light_A.green_time,
                "light_B_green_time": self.intersection.light_B.green_time,
            },
            "current_spawn_rates": {
                "lane_A": self.intersection.lane_A.get_traffic_info()[
                    "current_spawn_rate"
                ],
                "lane_B": self.intersection.lane_B.get_traffic_info()[
                    "current_spawn_rate"
                ],
            },
        }
