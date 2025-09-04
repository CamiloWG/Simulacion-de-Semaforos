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
            self._apply_rules_for_traffic_flow()

    def _apply_rules_for_traffic_flow(self):
        # Get counts for both lanes
        count_A = self.lane_A.count_approaching_within(self.d)
        count_B = self.lane_B.count_approaching_within(self.d)

        # Rule 1: Add to counter if light is red
        if self.light_A.state == "red":
            self.counter_A += count_A
        if self.light_B.state == "red":
            self.counter_B += count_B

        # Determine which lane should get green light
        target = self._determine_change_target(count_A, count_B)

        if target == "A" and self.light_A.state == "red":
            self._change_to_A()
        elif target == "B" and self.light_B.state == "red":
            self._change_to_B()

    def _determine_change_target(self, count_A, count_B):
        # Current green lane
        current_green_lane = (
            self.lane_A if self.light_A.state == "green" else self.lane_B
        )
        current_green_light = (
            self.light_A if self.light_A.state == "green" else self.light_B
        )

        # Check if a change is needed based on rules
        should_change = False

        # Rule 5: A car is stopped beyond e in the green direction -> change
        if current_green_lane.has_stopped_beyond_intersection_within(self.e):
            should_change = True

        # Rule 4: No cars in green, but at least one in red
        green_has_any_in_d = current_green_lane.count_approaching_within(self.d) > 0
        red_has_any_in_d = (
            count_A > 0 if current_green_lane == self.lane_B else count_B > 0
        )
        if (not green_has_any_in_d) and red_has_any_in_d:
            should_change = True

        # Rule 1 (cont.): The counter for the red light exceeds the threshold n
        counter_val = (
            self.counter_B if current_green_lane == self.lane_A else self.counter_A
        )
        if counter_val > self.n:
            should_change = True

        # Apply restrictions (Rule 2 and 3) before deciding the target
        if not should_change:
            return None

        # Rule 2: Must stay green for minimum time u
        if current_green_light.green_time < self.u:
            return None

        # Rule 3: Don't switch if a few cars are crossing
        close_to_cross = current_green_lane.count_within_r_to_cross(self.r)
        if close_to_cross <= self.m and close_to_cross > 0:
            return None

        # If all checks pass, determine the target based on need
        if self.light_A.state == "green":
            return "B"
        else:
            return "A"

    def _change_to_A(self):
        self.light_B.set_red()
        self.light_A.set_green()
        self.counter_B = 0

    def _change_to_B(self):
        self.light_A.set_red()
        self.light_B.set_green()
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
