# run_sim.py - Script principal con todas las mejoras implementadas
from semaforos.lane import Lane
from semaforos.intersection import Intersection
from semaforos.simulation import Simulation
from semaforos.gui import GUI


def main():
    """
    Simulación de semáforos auto-organizantes - Versión completamente mejorada

    MEJORAS IMPLEMENTADAS:
    ✅ Sistema de patrones de tráfico dinámicos con picos y valles aleatorios
    ✅ Implementación correcta de todas las 5 reglas del algoritmo
    ✅ Mejor lógica de movimiento de vehículos sin atascos erráticos
    ✅ Métricas de rendimiento y eficiencia mejoradas
    ✅ Interfaz gráfica más informativa y visualmente atractiva
    ✅ Sistema de debug para verificar funcionamiento de reglas

    REGLAS IMPLEMENTADAS:
    1. ✅ Contador acumulativo por vehículos esperando en semáforo rojo
    2. ✅ Tiempo mínimo obligatorio en verde antes de cambiar
    3. ✅ No cambiar si pocos vehículos están cerca de cruzar
    4. ✅ Cambiar si no hay tráfico en verde pero sí en rojo
    5. ✅ Cambiar si hay vehículos detenidos después del cruce
    6. ✅ Emergencia: ambos semáforos rojos si hay bloqueo cruzado
    """

    print("=" * 80)
    print("SIMULACIÓN DE SEMÁFOROS AUTO-ORGANIZANTES - VERSIÓN MEJORADA")
    print("=" * 80)
    print()
    print("🚀 NUEVAS CARACTERÍSTICAS:")
    print("  • Patrones de tráfico dinámicos con picos y valles")
    print("  • Implementación correcta de las 5 reglas del algoritmo")
    print("  • Vehículos con comportamiento realista")
    print("  • Métricas de rendimiento en tiempo real")
    print("  • Interfaz visual mejorada con indicadores de tráfico")
    print("  • Panel de debug para verificar el funcionamiento")
    print()

    # Configuración de carriles con patrones de tráfico más realistas
    lane_A = Lane(
        name="A",
        max_speed=1.8,  # Velocidad más realista
        lane_length=500.0,  # Carriles más largos para más vehículos
        min_gap_units=4.0,  # Separación más permisiva entre vehículos
        vehicle_length=4.0,  # Longitud más realista de vehículos
    )
    # El patrón de tráfico se configura automáticamente en __post_init__

    lane_B = Lane(
        name="B",
        max_speed=1.7,  # Velocidades ligeramente diferentes
        lane_length=500.0,
        min_gap_units=4.0,
        vehicle_length=4.0,
    )

    # Configuración del cruce con parámetros para tráfico más denso
    intersection = Intersection(
        lane_A=lane_A,
        lane_B=lane_B,
        d=180.0,  # Distancia de detección más amplia
        n=20,  # Umbral del contador más alto para más vehículos
        u=15,  # Tiempo mínimo en verde ajustado
        m=4,  # Más vehículos permitidos cerca para cambiar
        r=50.0,  # Distancia de restricción ajustada
        e=35.0,  # Distancia de emergencia
    )

    # Estado inicial: carril A en verde
    intersection.light_A.set_green()
    intersection.light_B.set_red()

    # Crear simulación
    simulation = Simulation(intersection=intersection, max_steps=2000000)

    # Crear interfaz gráfica mejorada
    gui = GUI(simulation, width=1400, height=900)

    print("📋 REGLAS DEL ALGORITMO:")
    print("  1. Acumular contador por vehículos esperando en rojo")
    print(f"     → Cambiar cuando contador ≥ {intersection.n}")
    print("  2. Mantener semáforo verde mínimo tiempo")
    print(f"     → Tiempo mínimo: {intersection.u} unidades")
    print("  3. No cambiar si pocos vehículos van a cruzar")
    print(f"     → Si ≤ {intersection.m} vehículos en zona r={intersection.r}")
    print("  4. Cambiar si no hay tráfico en verde pero sí en rojo")
    print(f"     → Detectar en distancia d={intersection.d}")
    print("  5. Cambiar si hay bloqueo después del cruce")
    print(f"     → Detectar en distancia e={intersection.e}")
    print("  6. Emergencia: ambos rojos si bloqueo cruzado")
    print()

    print("🎮 CONTROLES MEJORADOS:")
    print("  ESPACIO     - Pausar/Reanudar simulación")
    print("  ↑/↓         - Velocidad de simulación (1x-10x)")
    print("  ←/→         - Intensidad de picos de tráfico")
    print("  Z           - Mostrar/ocultar zonas D, R, E")
    print("  S           - Panel de estadísticas detalladas")
    print("  D           - Panel de debug (verificación de reglas)")
    print("  T           - Indicadores de patrones de tráfico")
    print("  R           - Reiniciar simulación")
    print("  ESC         - Salir")
    print()

    print("📊 MÉTRICAS DISPONIBLES:")
    print("  • Eficiencia del sistema (% vehículos completados)")
    print("  • Tiempo promedio de espera")
    print("  • Rendimiento por carril")
    print("  • Gráfico de throughput en tiempo real")
    print("  • Contadores de reglas en tiempo real")
    print()

    print("🎨 VISUALIZACIÓN:")
    print("  • Vehículos azules: Carril A (horizontal →)")
    print("  • Vehículos magenta: Carril B (vertical ↓)")
    print("  • Vehículos grises: Detenidos")
    print("  • Zona D (azul): Detección de vehículos")
    print("  • Zona R (naranja): Restricción para cambios")
    print("  • Zona E (roja): Detección de bloqueos")
    print("  • Indicadores de tráfico: Verde/Amarillo/Rojo")
    print()

    print("⚡ PATRONES DE TRÁFICO DINÁMICOS:")
    print("  • Carril A: Picos cada ~300 unidades, desfase 0")
    print("  • Carril B: Picos cada ~300 unidades, desfase 150")
    print("  • Variación aleatoria en tasas de spawn")
    print("  • Períodos de tráfico bajo y alto")
    print()

    print("🔧 PARÁMETROS OPTIMIZADOS PARA TRÁFICO MÚLTIPLE:")
    print(f"  • Velocidad máxima: A={lane_A.max_speed}, B={lane_B.max_speed}")
    print(f"  • Separación mínima: {lane_A.min_gap_units} unidades")
    print(f"  • Longitud carriles: {lane_A.lane_length} unidades")
    print(f"  • Tasas de spawn base: A=0.08, B=0.07")
    print(f"  • d = {intersection.d} (detección)")
    print(f"  • n = {intersection.n} (umbral contador)")
    print(f"  • u = {intersection.u} (tiempo mínimo verde)")
    print(f"  • m = {intersection.m} (vehículos cerca máx)")
    print(f"  • r = {intersection.r} (distancia restricción)")
    print(f"  • e = {intersection.e} (distancia emergencia)")
    print()

    print("✅ MEJORAS IMPLEMENTADAS:")
    print("  • Múltiples vehículos simultáneos por carril")
    print("  • Lógica individual de decisión por vehículo")
    print("  • Movimiento continuo a través del cruce")
    print("  • Spawn más permisivo (min_gap reducido)")
    print("  • Comportamiento realista de aceleración/frenado")
    print()

    print("Iniciando simulación mejorada...")
    print("=" * 80)

    try:
        # Ejecutar interfaz gráfica
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
