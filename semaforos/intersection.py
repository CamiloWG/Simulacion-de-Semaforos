# semaforos/intersection.py
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
        # parameters
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
        # 1) advance green timers
        self.light_A.step_time()
        self.light_B.step_time()

        # 2) Rule 6: cross-block beyond e
        stopped_A_beyond = self.lane_A.has_stopped_beyond_intersection_within(self.e)
        stopped_B_beyond = self.lane_B.has_stopped_beyond_intersection_within(self.e)

        if stopped_A_beyond and stopped_B_beyond:
            self.light_A.set_red()
            self.light_B.set_red()
            self.both_red = True
        elif self.both_red and not (stopped_A_beyond or stopped_B_beyond):
            self.both_red = False
            # Restore based on which lane has more need
            countA = self.lane_A.count_approaching_within(self.d)
            countB = self.lane_B.count_approaching_within(self.d)
            if countA >= countB:
                self.light_A.set_green()
                self.light_B.set_red()
            else:
                self.light_B.set_green()
                self.light_A.set_red()

        # 3) If not in emergency "both red" state, apply self-organizing rules
        if not self.both_red:
            self._apply_rules_for_direction(
                self.lane_A, self.lane_B, self.light_A, self.light_B, "A"
            )
            self._apply_rules_for_direction(
                self.lane_B, self.lane_A, self.light_B, self.light_A, "B"
            )

    def _apply_rules_for_direction(
        self,
        lane_red: Lane,
        lane_green: Lane,
        light_red: TrafficLight,
        light_green: TrafficLight,
        label: str,
    ):
        # Rule 1: Add to counter if light is red
        if light_red.state == "red":
            c = lane_red.count_approaching_within(self.d)
            if label == "A":
                self.counter_A += c
            else:
                self.counter_B += c

        # Check conditions for a switch, in order of priority

        # Rule 5: A car is stopped beyond e in the green direction -> change
        if lane_green.has_stopped_beyond_intersection_within(self.e):
            self._attempt_change(light_green, light_red, label)
            return

        # Rule 4: No cars in green direction, but at least one in red direction -> change
        green_has_any_in_d = lane_green.count_approaching_within(self.d) > 0
        red_has_any_in_d = lane_red.count_approaching_within(self.d) > 0
        if (not green_has_any_in_d) and red_has_any_in_d:
            self._attempt_change(light_green, light_red, label)
            return

        # Rule 1 (cont.): The counter for the red light exceeds the threshold n -> change
        counter_val = self.counter_A if label == "A" else self.counter_B
        if counter_val > self.n:
            self._attempt_change(light_green, light_red, label)
            return

    def _attempt_change(
        self, current_green: TrafficLight, current_red: TrafficLight, label: str
    ):
        # Rule 2: Must stay green for minimum time u
        if current_green.green_time < self.u:
            return

        # Rule 3: Don't switch if a few cars (m or less) are about to cross
        close_to_cross = (
            self.lane_A.count_within_r_to_cross(self.r)
            if current_green.name == "A"
            else self.lane_B.count_within_r_to_cross(self.r)
        )
        if close_to_cross <= self.m and close_to_cross > 0:
            return

        # If all checks pass, perform the switch instantly
        current_green.set_red()
        current_red.set_green()

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
