from semaforos.lane import Lane
from semaforos.intersection import Intersection
from semaforos.simulation import Simulation
from semaforos.gui import GUI


def main():

    print("=" * 80)
    print("SIMULACIÓN DE SEMÁFOROS AUTO-ORGANIZANTES - VERSIÓN MEJORADA")
    print("=" * 80)
    print()

    # Configuración de carriles con patrones de tráfico más realistas
    lane_A = Lane(
        name="A",
        max_speed=1.8,  # Velocidad más realista
        lane_length=600.0,  # Carriles más largos para más vehículos
        min_gap_units=1.8,  # Antes era 3.0 (reducido 40%)
        vehicle_length=3.5,  # Longitud más realista de vehículos
    )
    # El patrón de tráfico se configura automáticamente en __post_init__

    lane_B = Lane(
        name="B",
        max_speed=1.7,  # Velocidades ligeramente diferentes
        lane_length=600.0,
        min_gap_units=1.8,  # Antes era 3.0 (reducido 40%)
        vehicle_length=3.5,
    )

    intersection = Intersection(
        lane_A=lane_A,
        lane_B=lane_B,
        d=180.0,  # Distancia de detección más amplia
        n=20,  # Umbral del contador más alto para más vehículos
        u=220,  # Tiempo mínimo en verde ajustado
        m=4,  # Más vehículos permitidos cerca para cambiar
        r=50.0,  # Distancia de restricción ajustada
        e=35.0,  # Distancia de emergencia
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
