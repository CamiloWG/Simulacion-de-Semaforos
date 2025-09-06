# run_sim.py - Script principal corregido
from semaforos.lane import Lane
from semaforos.intersection import Intersection
from semaforos.simulation import Simulation
from semaforos.gui import GUI


def main():
    """
    Simulación de semáforos auto-organizantes - Versión corregida

    Correcciones principales:
    1. Los vehículos se detienen exactamente en las líneas del cruce cuando el semáforo está rojo
    2. Las zonas D, R, E están correctamente posicionadas respecto al verdadero cruce
    3. Lógica de movimiento mejorada que evita comportamientos erráticos
    4. Parámetros balanceados para una simulación realista
    """

    # Configuración de carriles con parámetros optimizados
    lane_A = Lane(
        name="A",
        spawn_rate=0.04,  # Spawn rate más conservador
        max_speed=1.0,  # Velocidad consistente
        lane_length=400.0,  # Longitud suficiente para colas
        min_gap_units=10.0,  # Separación generosa entre vehículos
    )

    lane_B = Lane(
        name="B",
        spawn_rate=0.05,  # Ligeramente diferente para asimetría
        max_speed=1.0,
        lane_length=400.0,
        min_gap_units=10.0,
    )

    # Configuración del cruce con parámetros balanceados
    intersection = Intersection(
        lane_A=lane_A,
        lane_B=lane_B,
        d=120.0,  # Distancia de detección - suficiente para detectar colas
        n=15,  # Umbral del contador - evita cambios muy frecuentes
        u=25,  # Tiempo mínimo en verde - permite que pasen varios vehículos
        m=2,  # Máximo vehículos cerca para no cambiar - más restrictivo
        r=40.0,  # Distancia de restricción - zona cerca del cruce
        e=25.0,  # Distancia de emergencia - detecta bloqueos
    )

    # Estado inicial del sistema
    intersection.light_A.set_green()
    intersection.light_B.set_red()

    # Crear simulación
    simulation = Simulation(intersection=intersection, max_steps=1000000)

    # Crear interfaz gráfica
    gui = GUI(simulation, width=1200, height=800)

    # Información para el usuario
    print("=" * 60)
    print("SIMULACIÓN DE SEMÁFOROS AUTO-ORGANIZANTES - VERSIÓN CORREGIDA")
    print("=" * 60)
    print()
    print("CORRECCIONES IMPLEMENTADAS:")
    print("✓ Los vehículos se detienen exactamente en las líneas punteadas del cruce")
    print("✓ Las zonas D, R, E están posicionadas correctamente")
    print("✓ Eliminado el comportamiento errático de los vehículos")
    print("✓ Las líneas punteadas BLANCAS definen el verdadero cruce")
    print()
    print("REGLAS DEL SISTEMA:")
    print("1. Contador por vehículos esperando en semáforo rojo")
    print("2. Tiempo mínimo obligatorio en verde")
    print("3. No cambiar si pocos vehículos van a cruzar")
    print("4. Cambiar si no hay tráfico en verde pero sí en rojo")
    print("5. Cambiar si hay bloqueo después del cruce")
    print("6. Emergencia: ambos rojos si hay bloqueo cruzado")
    print()
    print("CONTROLES:")
    print("  ESPACIO  - Pausar/Reanudar simulación")
    print("  ↑/↓      - Ajustar velocidad de simulación")
    print("  ←/→      - Ajustar tasa de generación de vehículos")
    print("  Z        - Mostrar/ocultar zonas D, R, E")
    print("  S        - Mostrar/ocultar panel de estadísticas")
    print("  R        - Reiniciar simulación")
    print("  ESC      - Salir del programa")
    print()
    print("INTERPRETACIÓN VISUAL:")
    print("• Vehículos AZULES: Carril A (movimiento horizontal →)")
    print("• Vehículos MAGENTA: Carril B (movimiento vertical ↓)")
    print("• Vehículos GRISES: Detenidos")
    print("• Zona D (azul): Área de detección de vehículos")
    print("• Zona R (naranja): Área de restricción para cambios")
    print("• Zona E (roja): Área de detección de bloqueos")
    print()
    print("Iniciando simulación...")
    print("=" * 60)

    # Ejecutar interfaz gráfica
    gui.run()


if __name__ == "__main__":
    main()
