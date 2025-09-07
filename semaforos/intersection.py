from .lane import Lane
from .light import TrafficLight


class Intersection:
    def __init__(
        self,
        lane_A: Lane,
        lane_B: Lane,
        d: float = 150.0,  # distancia para detectar vehículos aproximándose
        n: int = 10,  # umbral del contador para cambiar semáforo
        u: int = 15,  # tiempo mínimo en verde
        m: int = 2,  # máximo número de vehículos cerca para no cambiar
        r: float = 50.0,  # distancia corta para vehículos por cruzar
        e: float = 30.0,  # distancia para detectar bloqueos después del cruce
    ):
        self.lane_A = lane_A
        self.lane_B = lane_B
        self.light_A = TrafficLight(name=lane_A.name)
        self.light_B = TrafficLight(name=lane_B.name)

        # Parámetros del algoritmo
        self.d = d
        self.n = n
        self.u = u
        self.m = m
        self.r = r
        self.e = e

        # Líneas de parada para cada carril
        self.stop_line_A = 0.0
        self.stop_line_B = 0.0

        # Contadores para la Regla 1
        self.counter_A = 0
        self.counter_B = 0

        # Estado de emergencia
        self.both_red = False
        self.both_red_timer = 0

        # Estadísticas
        self.total_changes = 0
        self.last_change_reason = ""

    def step(self):
        """Ejecuta un paso de la simulación del cruce."""
        # 1) Avanzar contadores de tiempo verde
        self.light_A.step_time()
        self.light_B.step_time()

        # 2) Aplicar Regla 6: Bloqueo cruzado
        self._check_cross_blocking()

        # 3) Si no estamos en estado "ambos rojos", aplicar reglas de flujo
        if not self.both_red:
            self._apply_traffic_flow_rules()
        else:
            self.both_red_timer += 1

    def _check_cross_blocking(self):
        """Regla 6: Detectar bloqueo cruzado."""
        blocked_A = self.lane_A.has_stopped_beyond_intersection_within(self.e)
        blocked_B = self.lane_B.has_stopped_beyond_intersection_within(self.e)

        if blocked_A and blocked_B and not self.both_red:
            self.light_A.set_red()
            self.light_B.set_red()
            self.both_red = True
            self.both_red_timer = 0
            self.last_change_reason = "Regla 6: Bloqueo cruzado detectado"
            self.total_changes += 1

        elif (
            self.both_red and not (blocked_A and blocked_B) and self.both_red_timer > 5
        ):
            # Salir del estado de emergencia
            self.both_red = False
            count_A = self.lane_A.count_approaching_within(self.d)
            count_B = self.lane_B.count_approaching_within(self.d)

            if count_A >= count_B:
                self.light_A.set_green()
                self.light_B.set_red()
            else:
                self.light_B.set_green()
                self.light_A.set_red()

            self.last_change_reason = "Saliendo del bloqueo cruzado"
            self.total_changes += 1

    def _apply_traffic_flow_rules(self):
        """Aplica las reglas de flujo de tráfico correctamente."""
        # Contar vehículos en cada carril
        count_A = self.lane_A.count_approaching_within(self.d)
        count_B = self.lane_B.count_approaching_within(self.d)

        # REGLA 1: Incrementar contadores para semáforos en rojo
        if self.light_A.state == "red":
            self.counter_A += count_A
        if self.light_B.state == "red":
            self.counter_B += count_B

        # Determinar si necesitamos cambiar
        change_target = self._should_change_light(count_A, count_B)

        if change_target == "A" and self.light_A.state == "red":
            self._change_to_A()
        elif change_target == "B" and self.light_B.state == "red":
            self._change_to_B()

    def _should_change_light(self, count_A: int, count_B: int):
        """
        Determina si el semáforo debe cambiar aplicando todas las reglas correctamente.
        """
        current_green = "A" if self.light_A.state == "green" else "B"
        current_light = self.light_A if current_green == "A" else self.light_B
        current_lane = self.lane_A if current_green == "A" else self.lane_B
        other_lane = self.lane_B if current_green == "A" else self.lane_A

        should_change = False
        reason = ""

        # REGLA 5: Vehículo detenido más allá del cruce
        if current_lane.has_stopped_beyond_intersection_within(self.e):
            should_change = True
            reason = f"Regla 5: Vehículo detenido después del cruce en {current_green}"

        # REGLA 4: No hay vehículos aproximándose a luz verde, pero sí a luz roja
        green_approaching = count_A if current_green == "A" else count_B
        red_approaching = count_B if current_green == "A" else count_A

        if not should_change and green_approaching == 0 and red_approaching > 0:
            should_change = True
            reason = f"Regla 4: Sin tráfico aproximándose a {current_green}, pero {red_approaching} en rojo"

        # REGLA 1: El contador excede el umbral
        red_counter = self.counter_B if current_green == "A" else self.counter_A
        if not should_change and red_counter >= self.n:
            should_change = True
            reason = f"Regla 1: Contador excede umbral ({red_counter} >= {self.n})"

        if not should_change:
            return None

        # RESTRICCIONES antes de cambiar:

        # REGLA 2: Tiempo mínimo en verde
        if current_light.green_time < self.u:
            return None

        # REGLA 3: Pocos vehículos cerca de cruzar
        close_vehicles = current_lane.count_within_r_to_cross(self.r)
        if 0 < close_vehicles <= self.m:
            return None

        # Cambiar al otro semáforo
        self.last_change_reason = reason
        return "B" if current_green == "A" else "A"

    def _change_to_A(self):
        """Cambia para dar verde al carril A."""
        self.light_A.set_green()
        self.light_B.set_red()
        self.counter_A = 0
        self.total_changes += 1

    def _change_to_B(self):
        """Cambia para dar verde al carril B."""
        self.light_B.set_green()
        self.light_A.set_red()
        self.counter_B = 0
        self.total_changes += 1

    def get_state(self):
        """Retorna el estado actual del cruce."""
        return {
            "light_A": self.light_A.state,
            "light_A_gtime": self.light_A.green_time,
            "light_B": self.light_B.state,
            "light_B_gtime": self.light_B.green_time,
            "counter_A": self.counter_A,
            "counter_B": self.counter_B,
            "both_red": self.both_red,
            "both_red_timer": self.both_red_timer,
            "total_changes": self.total_changes,
            "last_change_reason": self.last_change_reason,
            "vehicles_A": self.lane_A.get_vehicle_count(),
            "vehicles_B": self.lane_B.get_vehicle_count(),
            "waiting_A": self.lane_A.get_waiting_vehicles(),
            "waiting_B": self.lane_B.get_waiting_vehicles(),
        }
