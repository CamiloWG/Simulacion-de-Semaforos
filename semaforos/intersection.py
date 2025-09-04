from .lane import Lane
from .light import TrafficLight


class Intersection:
    def __init__(
        self,
        lane_A: Lane,
        lane_B: Lane,
        d: float = 120.0,
        n: int = 6,
        u: int = 5,
        m: int = 1,
        r: float = 40.0,
        e: float = 30.0,
    ):
        self.lane_A = lane_A
        self.lane_B = lane_B
        self.light_A = TrafficLight(name=lane_A.name)
        self.light_B = TrafficLight(name=lane_B.name)
        # parámetros
        self.d = d
        self.n = n
        self.u = u
        self.m = m
        self.r = r
        self.e = e
        self.counter_A = 0
        self.counter_B = 0
        self.both_red = False

        # Para manejar la transición verde->amarillo->otro verde sin hacer swap instantáneo
        self.pending_switch = (
            None  # {'target': 'A' or 'B', 'timer': int, 'from': 'A' or 'B'}
        )

    def step(self):
        # si hay una transición pendiente, disminuir timer y completar cuando llegue a 0
        if self.pending_switch:
            self.pending_switch["timer"] -= 1
            if self.pending_switch["timer"] <= 0:
                # realizar el cambio final: target en verde, otro en red
                target = self.pending_switch["target"]
                if target == "A":
                    self.light_A.set_green()
                    self.light_B.set_red()
                else:
                    self.light_B.set_green()
                    self.light_A.set_red()
                # reset contadores cuando cambia
                self.counter_A = 0
                self.counter_B = 0
                self.pending_switch = None

        # avanzar timers de verde
        self.light_A.step_time()
        self.light_B.step_time()

        # aplicar reglas si no hay transición pendiente
        if not self.pending_switch:
            self._apply_rules_for_direction(
                self.lane_A, self.lane_B, self.light_A, self.light_B, "A"
            )
            self._apply_rules_for_direction(
                self.lane_B, self.lane_A, self.light_B, self.light_A, "B"
            )

        # regla 6: bloqueo cruzado beyond e
        stopped_A_beyond = self.lane_A.has_stopped_beyond_intersection_within(self.e)
        stopped_B_beyond = self.lane_B.has_stopped_beyond_intersection_within(self.e)
        if stopped_A_beyond and stopped_B_beyond:
            # ambas rojas (emergencia)
            self.light_A.set_red()
            self.light_B.set_red()
            self.both_red = True
            # cancelar pending_switch si existiera
            self.pending_switch = None
            return
        else:
            if self.both_red and not (stopped_A_beyond and stopped_B_beyond):
                # restaurar la dirección con más necesidad
                self.both_red = False
                countA = self.lane_A.count_approaching_within(self.d)
                countB = self.lane_B.count_approaching_within(self.d)
                if countA >= countB:
                    self.light_A.set_green()
                    self.light_B.set_red()
                else:
                    self.light_B.set_green()
                    self.light_A.set_red()

    def _apply_rules_for_direction(
        self,
        lane_red: Lane,
        lane_green: Lane,
        light_red: TrafficLight,
        light_green: TrafficLight,
        label: str,
    ):
        # regla 1 contador (cuando luz roja)
        if light_red.state == "red":
            c = lane_red.count_approaching_within(self.d)
            if c > 0:
                if label == "A":
                    self.counter_A += c
                else:
                    self.counter_B += c
            counter_val = self.counter_A if label == "A" else self.counter_B
            if counter_val > self.n:
                # regla 2: respetar tiempo minimo en verde de la otra direccion
                if light_green.green_time < self.u:
                    return
                # regla 3: si pocos vehiculos en r en la direccion verde, no cambiar
                close_to_cross = lane_green.count_within_r_to_cross(self.r)
                if close_to_cross <= self.m and close_to_cross > 0:
                    return
                # regla 4: si no hay en verde dentro d y hay en roja dentro d, cambiar
                green_has_any_in_d = lane_green.count_approaching_within(self.d) > 0
                red_has_any_in_d = lane_red.count_approaching_within(self.d) > 0
                if (not green_has_any_in_d) and red_has_any_in_d:
                    self._request_change(light_green, light_red, label)
                    return
                # regla 5: bloqueo beyond e en direc verde -> cambiar
                if lane_green.has_stopped_beyond_intersection_within(self.e):
                    self._request_change(light_green, light_red, label)
                    return
                # por contador, solicitar cambio
                self._request_change(light_green, light_red, label)
                return

        # regla 4 alternativa: si direccion verde no tiene vehiculos dentro d y roja si, y green_time >= u
        if light_green.state == "green":
            green_has_any_in_d = lane_green.count_approaching_within(self.d) > 0
            red_has_any_in_d = lane_red.count_approaching_within(self.d) > 0
            if (
                (not green_has_any_in_d)
                and red_has_any_in_d
                and light_green.green_time >= self.u
            ):
                close_to_cross = lane_green.count_within_r_to_cross(self.r)
                if close_to_cross <= self.m and close_to_cross > 0:
                    return
                self._request_change(light_green, light_red, label)
                return

        # regla 5: bloqueo beyond e
        if (
            lane_green.has_stopped_beyond_intersection_within(self.e)
            and light_green.green_time >= self.u
        ):
            self._request_change(light_green, light_red, label)
            return

    def _request_change(
        self, current_green: TrafficLight, current_red: TrafficLight, label: str
    ):
        """
        En lugar de hacer swap instantáneo, lanzamos la fase amarilla en la dirección que está en verde
        y programamos el cambio final al otro en pending_switch.
        """
        # si ya hay pending, no hacemos nada
        if self.pending_switch:
            return

        # si current_green está en verde -> lo mandamos a amarillo y programamos el target
        if current_green.state == "green":
            current_green.state = "yellow"
            # timer de espera = tiempo de amarillo configurado en la luz que está cambiando
            timer = (
                current_green.yellow_time_config
                if hasattr(current_green, "yellow_time_config")
                else 2
            )
            # target será la dirección opuesta (label indica el candidato que pidió el cambio: 'A' si lane_red es A)
            target = (
                "A" if label == "A" else "B"
            )  # label indica cuál roja solicita cambio
            # Pero label logic: when applying for lane_red label == 'A', target should be 'A'
            # timer cuenta para la luz que está en amarillo (la que era green)
            self.pending_switch = {
                "target": target,
                "timer": timer,
                "from": "A" if current_green == self.light_A else "B",
            }
        else:
            # si current_green no está en green (por ejemplo ambas rojas), hacer cambio inmediato
            if label == "A":
                self.light_A.set_green()
                self.light_B.set_red()
                self.counter_A = 0
                self.counter_B = 0
            else:
                self.light_B.set_green()
                self.light_A.set_red()
                self.counter_A = 0
                self.counter_B = 0

    def get_state(self):
        return {
            "light_A": self.light_A.state,
            "light_A_gtime": self.light_A.green_time,
            "light_B": self.light_B.state,
            "light_B_gtime": self.light_B.green_time,
            "counter_A": self.counter_A,
            "counter_B": self.counter_B,
            "both_red": self.both_red,
            "pending_switch": self.pending_switch,
        }
