from semaforos.lane import Lane
from semaforos.intersection import Intersection
from semaforos.simulation import Simulation
from semaforos.gui import GUI


def main():
    laneA = Lane(
        name="A", spawn_rate=0.06, max_speed=1.0, lane_length=400.0, min_gap_units=6.0
    )
    laneB = Lane(
        name="B", spawn_rate=0.06, max_speed=1.0, lane_length=400.0, min_gap_units=6.0
    )
    inter = Intersection(
        lane_A=laneA, lane_B=laneB, d=150.0, n=6, u=20, m=1, r=50.0, e=30.0
    )
    inter.light_A.set_green()
    inter.light_B.set_red()
    sim = Simulation(intersection=inter, max_steps=100000)
    gui = GUI(sim)
    gui.run()


if __name__ == "__main__":
    main()
