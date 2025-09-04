from .lane import Lane
from .light import TrafficLight


class Intersection:
    def __init__(
        self,
        lane_A: Lane,
        lane_B: Lane,
        d: float = 50.0,
        n: int = 5,
        u: int = 5,
        m: int = 1,
        r: float = 5.0,
        e: float = 5.0,
    ):
        self.lane_A = lane_A
        self.lane_B = lane_B
        self.light_A = TrafficLight(name=lane_A.name)
        self.light_B = TrafficLight(name=lane_B.name)
        self.d = d
        self.n = n
        self.u = u
        self.m = m
        self.r = r
        self.e = e
        self.counter_A = 0
        self.counter_B = 0
        self.both_red = False

    def step(self):
        self.light_A.step_time()
        self.light_B.step_time()
        self._apply_rules_for_direction(
            self.lane_A, self.lane_B, self.light_A, self.light_B, "A"
        )
        self._apply_rules_for_direction(
            self.lane_B, self.lane_A, self.light_B, self.light_A, "B"
        )

        stopped_A_beyond = self.lane_A.has_stopped_beyond_intersection_within(self.e)
        stopped_B_beyond = self.lane_B.has_stopped_beyond_intersection_within(self.e)
        if stopped_A_beyond and stopped_B_beyond:
            self.light_A.set_red()
            self.light_B.set_red()
            self.both_red = True
            return
        else:
            if self.both_red:
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
        if light_red.state == "red":
            c = lane_red.count_approaching_within(self.d)
            if c > 0:
                if label == "A":
                    self.counter_A += c
                else:
                    self.counter_B += c
            counter_val = self.counter_A if label == "A" else self.counter_B
            if counter_val > self.n:
                if light_green.green_time < self.u:
                    return
                close_to_cross = lane_green.count_within_r_to_cross(self.r)
                if close_to_cross <= self.m and close_to_cross > 0:
                    return
                green_has_any_in_d = lane_green.count_approaching_within(self.d) > 0
                red_has_any_in_d = lane_red.count_approaching_within(self.d) > 0
                if (not green_has_any_in_d) and red_has_any_in_d:
                    self._change_to_green(light_red, light_green, label)
                    return
                if lane_green.has_stopped_beyond_intersection_within(self.e):
                    self._change_to_green(light_red, light_green, label)
                    return
                self._change_to_green(light_red, light_green, label)
                return

        if light_green.state == "green":
            green_has_any_in_d = lane_green.count_approaching_within(self.d) > 0
            red_has_any_in_d = lane_red.count_approaching_within(self.d) > 0
            if (not green_has_any_in_d) and red_has_any_in_d:
                if light_green.green_time >= self.u:
                    close_to_cross = lane_green.count_within_r_to_cross(self.r)
                    if close_to_cross <= self.m and close_to_cross > 0:
                        return
                    self._change_to_green(light_red, light_green, label)
                    return

        if lane_green.has_stopped_beyond_intersection_within(self.e):
            if light_green.green_time >= self.u:
                self._change_to_green(light_red, light_green, label)
                return

    def _change_to_green(
        self, light_to_turn_green: TrafficLight, other_light: TrafficLight, label: str
    ):
        light_to_turn_green.set_green()
        other_light.set_red()
        if label == "A":
            self.counter_A = 0
            self.counter_B = 0
        else:
            self.counter_B = 0
            self.counter_A = 0

    def get_state(self):
        return {
            "light_A": self.light_A.state,
            "light_A_gtime": self.light_A.green_time,
            "light_B": self.light_B.state,
            "light_B_gtime": self.light_B.green_time,
            "counter_A": self.counter_A,
            "counter_B": self.counter_B,
            "both_red": self.both_red,
        }
