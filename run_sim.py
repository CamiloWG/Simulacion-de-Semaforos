from semaforos.lane import Lane
from semaforos.intersection import Intersection
from semaforos.simulation import Simulation
from semaforos.gui import GUI


def main():

    print("=" * 80)
    print("SIMULACIÓN DE SEMÁFOROS AUTO-ORGANIZANTES")
    print("=" * 80)
    print()

    # Configuración de carriles
    lane_A = Lane(
        name="A",
        max_speed=1.8,
        lane_length=600.0,
        min_gap_units=1.8,
        vehicle_length=3.5,
    )

    lane_B = Lane(
        name="B",
        max_speed=1.7,
        lane_length=600.0,
        min_gap_units=1.8,
        vehicle_length=3.5,
    )

    intersection = Intersection(
        lane_A=lane_A, lane_B=lane_B, d=180.0, n=20, u=220, m=4, r=50.0, e=35.0
    )

    intersection.light_A.set_green()
    intersection.light_B.set_red()

    simulation = Simulation(intersection=intersection, max_steps=2000000)

    gui = GUI(simulation, width=1400, height=900)
    try:
        gui.run()
    except KeyboardInterrupt:
        print("\nSimulación interrumpida por el usuario.")
    except Exception as e:
        print(f"\nError durante la simulación: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\nSimulación finalizada.")


if __name__ == "__main__":
    main()
