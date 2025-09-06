# semaforos/gui.py - Interfaz corregida
"""
Interfaz gráfica corregida para la simulación.

Correcciones principales:
1. El cruce está definido por las líneas punteadas blancas, no las negras
2. Los vehículos se detienen exactamente en las líneas punteadas cuando el semáforo está rojo
3. Las zonas D, R, E están correctamente posicionadas respecto al verdadero cruce
4. Mejor lógica de movimiento que evita el comportamiento errático
"""

import pygame
import sys
from .simulation import Simulation
from .lane import Lane

# Colores
WHITE = (250, 250, 250)
BLACK = (10, 10, 10)
ROAD = (200, 200, 200)
LANE_MARK = (255, 255, 255)  # Blanco puro para las líneas punteadas
RED = (220, 50, 50)
GREEN = (50, 200, 80)
YELLOW = (240, 200, 60)
BLUE = (60, 110, 200)
MAGENTA = (170, 70, 170)
DARK_GREY = (120, 120, 120)
LIGHT_GREY = (180, 180, 180)

# Zonas (RGBA) - más sutiles
ZONE_D = (100, 150, 255, 60)  # azul para detección
ZONE_R = (255, 200, 100, 60)  # naranja para restricción
ZONE_E = (255, 100, 100, 60)  # rojo para emergencia


class GUI:
    def __init__(self, sim: Simulation, width: int = 1200, height: int = 800):
        pygame.init()
        self.sim = sim
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Semáforos Auto-organizantes - Simulación Corregida")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.small_font = pygame.font.SysFont("Arial", 12)

        # Coordenadas del cruce (centro de la pantalla)
        self.center_x = width // 2
        self.center_y = height // 2
        self.road_width = 160  # Ancho total de la carretera
        self.lane_width = 40  # Ancho de cada carril

        # Las líneas punteadas definen el VERDADERO cruce
        self.intersection_size = 120  # Tamaño del área de cruce

        # Líneas de parada (donde se detienen los vehículos con semáforo rojo)
        self.stop_line_A_x = self.center_x - self.intersection_size // 2
        self.stop_line_B_y = self.center_y - self.intersection_size // 2

        # Tamaños de vehículos
        self.vehicle_w = 28
        self.vehicle_h = 16
        self.min_pixel_gap = 6

        # Controles
        self.paused = False
        self.speedup = 1
        self.show_zones = True
        self.show_stats = True

    def _map_position_A_to_pixel(self, position: float, lane: Lane) -> int:
        """
        Mapea posición del carril A (horizontal) a coordenada X.
        position = 0 es exactamente la línea de parada del cruce.
        """
        if position >= 0:
            # Acercándose desde la izquierda hacia la línea de parada
            frac = min(position / max(1.0, lane.lane_length), 1.0)
            x = int(self.stop_line_A_x - frac * (self.stop_line_A_x - 50))
        else:
            # Ya cruzó, moviéndose hacia la derecha
            frac = min((-position) / max(1.0, lane.lane_length), 1.0)
            x = int(
                self.stop_line_A_x
                + self.intersection_size
                + frac * (self.width - self.stop_line_A_x - self.intersection_size - 50)
            )
        return x

    def _map_position_B_to_pixel(self, position: float, lane: Lane) -> int:
        """
        Mapea posición del carril B (vertical) a coordenada Y.
        position = 0 es exactamente la línea de parada del cruce.
        """
        if position >= 0:
            # Acercándose desde arriba hacia la línea de parada
            frac = min(position / max(1.0, lane.lane_length), 1.0)
            y = int(self.stop_line_B_y - frac * (self.stop_line_B_y - 50))
        else:
            # Ya cruzó, moviéndose hacia abajo
            frac = min((-position) / max(1.0, lane.lane_length), 1.0)
            y = int(
                self.stop_line_B_y
                + self.intersection_size
                + frac
                * (self.height - self.stop_line_B_y - self.intersection_size - 50)
            )
        return y

    def _draw_road_infrastructure(self):
        """Dibuja la infraestructura de la carretera."""
        # Carretera horizontal completa
        pygame.draw.rect(
            self.screen,
            ROAD,
            (0, self.center_y - self.road_width // 2, self.width, self.road_width),
        )

        # Carretera vertical completa
        pygame.draw.rect(
            self.screen,
            ROAD,
            (self.center_x - self.road_width // 2, 0, self.road_width, self.height),
        )

        # Dibujar las líneas punteadas que definen el VERDADERO cruce
        self._draw_intersection_boundaries()

        # Dibujar líneas divisorias de carriles (líneas negras finas en el centro)
        self._draw_lane_dividers()

    def _draw_intersection_boundaries(self):
        """
        Dibuja las líneas punteadas BLANCAS que definen el área de cruce.
        Estas son las líneas de referencia para los semáforos.
        """
        dash_w, gap = 20, 12

        # Líneas horizontales del cruce (arriba y abajo)
        y_top = self.center_y - self.intersection_size // 2
        y_bottom = self.center_y + self.intersection_size // 2

        # Línea superior del cruce
        x = 20
        while x < self.width:
            if not (
                self.center_x - self.intersection_size // 2
                <= x
                <= self.center_x + self.intersection_size // 2
            ):
                pygame.draw.rect(self.screen, LANE_MARK, (x, y_top - 3, dash_w, 6))
            x += dash_w + gap

        # Línea inferior del cruce
        x = 20
        while x < self.width:
            if not (
                self.center_x - self.intersection_size // 2
                <= x
                <= self.center_x + self.intersection_size // 2
            ):
                pygame.draw.rect(self.screen, LANE_MARK, (x, y_bottom - 3, dash_w, 6))
            x += dash_w + gap

        # Líneas verticales del cruce (izquierda y derecha)
        x_left = self.center_x - self.intersection_size // 2
        x_right = self.center_x + self.intersection_size // 2

        # Línea izquierda del cruce
        y = 20
        while y < self.height:
            if not (
                self.center_y - self.intersection_size // 2
                <= y
                <= self.center_y + self.intersection_size // 2
            ):
                pygame.draw.rect(self.screen, LANE_MARK, (x_left - 3, y, 6, dash_w))
            y += dash_w + gap

        # Línea derecha del cruce
        y = 20
        while y < self.height:
            if not (
                self.center_y - self.intersection_size // 2
                <= y
                <= self.center_y + self.intersection_size // 2
            ):
                pygame.draw.rect(self.screen, LANE_MARK, (x_right - 3, y, 6, dash_w))
            y += dash_w + gap

    def _draw_lane_dividers(self):
        """Dibuja las líneas divisorias finas en el centro de las carreteras."""
        # Línea divisoria horizontal
        pygame.draw.line(
            self.screen, LIGHT_GREY, (0, self.center_y), (self.width, self.center_y), 2
        )

        # Línea divisoria vertical
        pygame.draw.line(
            self.screen, LIGHT_GREY, (self.center_x, 0), (self.center_x, self.height), 2
        )

    def _draw_zones(self):
        """Dibuja las zonas D, R, E correctamente posicionadas."""
        if not self.show_zones:
            return

        inter = self.sim.intersection
        d, r, e = inter.d, inter.r, inter.e

        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Conversión de distancias a píxeles
        def dist_to_pixels_h(dist):
            return int((dist / inter.lane_A.lane_length) * (self.stop_line_A_x - 50))

        def dist_to_pixels_v(dist):
            return int((dist / inter.lane_B.lane_length) * (self.stop_line_B_y - 50))

        # Zonas para carril A (horizontal)
        px_d = dist_to_pixels_h(d)
        px_r = dist_to_pixels_h(r)
        px_e = dist_to_pixels_h(e)

        # Zona D (detección) - antes del cruce
        if px_d > 0:
            zone_d_rect = (
                self.stop_line_A_x - px_d,
                self.center_y - self.lane_width,
                px_d,
                self.lane_width * 2,
            )
            surf.fill(ZONE_D, zone_d_rect)

        # Zona R (restricción) - cerca del cruce
        if px_r > 0:
            zone_r_rect = (
                self.stop_line_A_x - px_r,
                self.center_y - self.lane_width,
                px_r,
                self.lane_width * 2,
            )
            surf.fill(ZONE_R, zone_r_rect)

        # Zona E (emergencia) - después del cruce
        if px_e > 0:
            zone_e_rect = (
                self.stop_line_A_x + self.intersection_size,
                self.center_y - self.lane_width,
                px_e,
                self.lane_width * 2,
            )
            surf.fill(ZONE_E, zone_e_rect)

        # Zonas para carril B (vertical)
        py_d = dist_to_pixels_v(d)
        py_r = dist_to_pixels_v(r)
        py_e = dist_to_pixels_v(e)

        # Zona D (detección)
        if py_d > 0:
            zone_d_rect = (
                self.center_x - self.lane_width,
                self.stop_line_B_y - py_d,
                self.lane_width * 2,
                py_d,
            )
            surf.fill(ZONE_D, zone_d_rect)

        # Zona R (restricción)
        if py_r > 0:
            zone_r_rect = (
                self.center_x - self.lane_width,
                self.stop_line_B_y - py_r,
                self.lane_width * 2,
                py_r,
            )
            surf.fill(ZONE_R, zone_r_rect)

        # Zona E (emergencia)
        if py_e > 0:
            zone_e_rect = (
                self.center_x - self.lane_width,
                self.stop_line_B_y + self.intersection_size,
                self.lane_width * 2,
                py_e,
            )
            surf.fill(ZONE_E, zone_e_rect)

        self.screen.blit(surf, (0, 0))

        # Etiquetas de las zonas
        self._draw_zone_labels()

    def _draw_zone_labels(self):
        """Dibuja etiquetas identificando las zonas."""
        # Etiquetas para carril A
        label_y = self.center_y - self.lane_width - 20

        # Zona D
        d_label = self.small_font.render("D", True, BLACK)
        self.screen.blit(d_label, (self.stop_line_A_x - 100, label_y))

        # Zona R
        r_label = self.small_font.render("R", True, BLACK)
        self.screen.blit(r_label, (self.stop_line_A_x - 30, label_y))

        # Zona E
        e_label = self.small_font.render("E", True, BLACK)
        self.screen.blit(
            e_label, (self.stop_line_A_x + self.intersection_size + 10, label_y)
        )

        # Etiquetas para carril B
        label_x = self.center_x - self.lane_width - 20

        d_label = self.small_font.render("D", True, BLACK)
        self.screen.blit(d_label, (label_x, self.stop_line_B_y - 100))

        r_label = self.small_font.render("R", True, BLACK)
        self.screen.blit(r_label, (label_x, self.stop_line_B_y - 30))

        e_label = self.small_font.render("E", True, BLACK)
        self.screen.blit(
            e_label, (label_x, self.stop_line_B_y + self.intersection_size + 10)
        )

    def _draw_vehicles(self):
        """Dibuja todos los vehículos con posicionamiento correcto."""
        # Dibujar vehículos del carril A (horizontal)
        self._draw_lane_A_vehicles()

        # Dibujar vehículos del carril B (vertical)
        self._draw_lane_B_vehicles()

    def _draw_lane_A_vehicles(self):
        """Dibuja vehículos del carril A con separación adecuada."""
        lane_a = self.sim.intersection.lane_A
        if not lane_a.vehicles:
            return

        # Separar vehículos por su posición respecto al cruce
        approaching = [v for v in lane_a.vehicles if v.position >= 0]
        crossing = [v for v in lane_a.vehicles if v.position < 0]

        y_position = self.center_y - self.lane_width // 2

        # Dibujar vehículos que se acercan (con separación visual)
        if approaching:
            approaching.sort(key=lambda v: v.position)
            pixel_positions = []

            for v in approaching:
                x = self._map_position_A_to_pixel(v.position, lane_a)

                # Aplicar separación mínima visual
                if pixel_positions:
                    min_x = pixel_positions[-1] - (self.vehicle_w + self.min_pixel_gap)
                    if x > min_x:
                        x = min_x

                pixel_positions.append(x)
                self._draw_vehicle(v, x, y_position, True)

        # Dibujar vehículos que ya cruzaron
        for v in crossing:
            x = self._map_position_A_to_pixel(v.position, lane_a)
            self._draw_vehicle(v, x, y_position, True)

    def _draw_lane_B_vehicles(self):
        """Dibuja vehículos del carril B con separación adecuada."""
        lane_b = self.sim.intersection.lane_B
        if not lane_b.vehicles:
            return

        approaching = [v for v in lane_b.vehicles if v.position >= 0]
        crossing = [v for v in lane_b.vehicles if v.position < 0]

        x_position = self.center_x + self.lane_width // 2

        # Dibujar vehículos que se acercan
        if approaching:
            approaching.sort(key=lambda v: v.position)
            pixel_positions = []

            for v in approaching:
                y = self._map_position_B_to_pixel(v.position, lane_b)

                # Aplicar separación mínima visual
                if pixel_positions:
                    min_y = pixel_positions[-1] - (self.vehicle_h + self.min_pixel_gap)
                    if y > min_y:
                        y = min_y

                pixel_positions.append(y)
                self._draw_vehicle(v, x_position, y, False)

        # Dibujar vehículos que ya cruzaron
        for v in crossing:
            y = self._map_position_B_to_pixel(v.position, lane_b)
            self._draw_vehicle(v, x_position, y, False)

    def _draw_vehicle(self, vehicle, x, y, is_horizontal):
        """Dibuja un vehículo individual."""
        # Color según el carril y estado
        if is_horizontal:
            base_color = BLUE
        else:
            base_color = MAGENTA

        color = base_color if not vehicle.stopped else DARK_GREY

        # Dibujar rectángulo del vehículo
        rect = pygame.Rect(
            x - self.vehicle_w // 2,
            y - self.vehicle_h // 2,
            self.vehicle_w,
            self.vehicle_h,
        )
        pygame.draw.rect(self.screen, color, rect, border_radius=4)
        pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=4)

        # Flecha direccional
        if is_horizontal:
            # Flecha hacia la derecha
            arrow_points = [
                (x + self.vehicle_w // 2 - 8, y),
                (x + self.vehicle_w // 2 - 2, y - 4),
                (x + self.vehicle_w // 2 - 2, y + 4),
            ]
        else:
            # Flecha hacia abajo
            arrow_points = [
                (x, y + self.vehicle_h // 2 - 8),
                (x - 4, y + self.vehicle_h // 2 - 2),
                (x + 4, y + self.vehicle_h // 2 - 2),
            ]

        pygame.draw.polygon(self.screen, WHITE, arrow_points)

    def _draw_traffic_lights(self):
        """Dibuja los semáforos en las posiciones correctas."""
        inter = self.sim.intersection

        # Semáforo para carril A (lado izquierdo del cruce)
        light_a_x = self.stop_line_A_x - 60
        light_a_y = self.center_y - 45
        self._draw_traffic_light(inter.light_A, light_a_x, light_a_y, "A")

        # Semáforo para carril B (lado superior del cruce)
        light_b_x = self.center_x - 20
        light_b_y = self.stop_line_B_y - 100
        self._draw_traffic_light(inter.light_B, light_b_x, light_b_y, "B")

    def _draw_traffic_light(self, light, x, y, name):
        """Dibuja un semáforo individual."""
        width, height = 35, 90

        # Fondo del semáforo
        pygame.draw.rect(
            self.screen, (40, 40, 40), (x, y, width, height), border_radius=6
        )
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 3, border_radius=6)

        # Luces
        colors = [RED, YELLOW, GREEN]
        states = ["red", "yellow", "green"]

        for i, (color, state) in enumerate(zip(colors, states)):
            center_y = y + 18 + i * 25
            radius = 10

            is_on = light.state == state
            draw_color = color if is_on else (60, 60, 60)

            pygame.draw.circle(
                self.screen, draw_color, (x + width // 2, center_y), radius
            )
            pygame.draw.circle(
                self.screen, BLACK, (x + width // 2, center_y), radius, 2
            )

        # Información del semáforo
        info = f"{name}: {light.state} (t={light.green_time})"
        text = self.small_font.render(info, True, BLACK)
        self.screen.blit(text, (x - 5, y + height + 5))

    def _draw_hud(self):
        """Dibuja la interfaz de usuario."""
        stats = self.sim.get_statistics()
        inter_state = stats["intersection_state"]

        # Información principal
        info_lines = [
            f"Tiempo: {stats['time']} | {'PAUSADO' if self.paused else f'Velocidad: {self.speedup}x'}",
            f"Vehículos: Generados={stats['total_spawned']} | Completados={stats['total_completed']} | Eficiencia={stats['efficiency']:.1f}%",
            f"Contadores: A={inter_state['counter_A']} | B={inter_state['counter_B']} | Cambios: {inter_state['total_changes']}",
        ]

        if inter_state["both_red"]:
            info_lines.append("⚠️ EMERGENCIA: Bloqueo cruzado detectado")

        if inter_state["last_change_reason"]:
            info_lines.append(f"Último cambio: {inter_state['last_change_reason']}")

        # Fondo del HUD
        hud_height = len(info_lines) * 22 + 20
        hud_rect = pygame.Rect(10, 10, self.width - 20, hud_height)
        pygame.draw.rect(self.screen, (255, 255, 255, 230), hud_rect)
        pygame.draw.rect(self.screen, BLACK, hud_rect, 2)

        # Texto del HUD
        y = 20
        for line in info_lines:
            color = RED if "EMERGENCIA" in line else BLACK
            text_surf = self.font.render(line, True, color)
            self.screen.blit(text_surf, (20, y))
            y += 22

        # Panel de controles
        self._draw_controls()

        # Panel de estadísticas (si está habilitado)
        if self.show_stats:
            self._draw_stats_panel(stats)

    def _draw_controls(self):
        """Dibuja la ayuda de controles."""
        controls = [
            "CONTROLES:",
            "ESPACIO: Pausar/Reanudar",
            "↑/↓: Velocidad",
            "←/→: Spawn rate",
            "Z: Zonas on/off",
            "S: Stats on/off",
            "R: Reiniciar",
            "ESC: Salir",
        ]

        y_start = self.height - len(controls) * 16 - 10
        for i, line in enumerate(controls):
            font = self.font if i == 0 else self.small_font
            color = DARK_GREY if i == 0 else BLACK
            text = font.render(line, True, color)
            self.screen.blit(text, (20, y_start + i * 16))

    def _draw_stats_panel(self, stats):
        """Dibuja panel de estadísticas detalladas."""
        inter_state = stats["intersection_state"]

        stat_lines = [
            "ESTADÍSTICAS DETALLADAS",
            f"Vehículos A: {inter_state['vehicles_A']} (esperando: {inter_state['waiting_A']})",
            f"Vehículos B: {inter_state['vehicles_B']} (esperando: {inter_state['waiting_B']})",
            f"Tiempos verde: A={inter_state['light_A_gtime']} | B={inter_state['light_B_gtime']}",
            f"Spawn rates: A={self.sim.intersection.lane_A.spawn_rate:.3f} | B={self.sim.intersection.lane_B.spawn_rate:.3f}",
            "",
            "PARÁMETROS:",
            f"d={self.sim.intersection.d} (detección)",
            f"n={self.sim.intersection.n} (umbral contador)",
            f"u={self.sim.intersection.u} (tiempo mín verde)",
            f"m={self.sim.intersection.m} (vehículos cerca máx)",
            f"r={self.sim.intersection.r} (distancia restricción)",
            f"e={self.sim.intersection.e} (distancia emergencia)",
        ]

        # Panel en el lado derecho
        panel_width = 300
        panel_height = len(stat_lines) * 16 + 20
        panel_x = self.width - panel_width - 10
        panel_y = 150

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (255, 255, 255, 240), panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)

        # Texto del panel
        y = panel_y + 10
        for line in stat_lines:
            if line == "":
                y += 8
                continue

            font = (
                self.font
                if "ESTADÍSTICAS" in line or "PARÁMETROS" in line
                else self.small_font
            )
            color = (
                DARK_GREY if "ESTADÍSTICAS" in line or "PARÁMETROS" in line else BLACK
            )
            text = font.render(line, True, color)
            self.screen.blit(text, (panel_x + 10, y))
            y += 16

        # Leyenda de colores
        self._draw_legend(panel_x, y + 10)

    def _draw_legend(self, x, y):
        """Dibuja leyenda de colores y símbolos."""
        legend_items = [
            (BLUE, "Vehículos A (→)"),
            (MAGENTA, "Vehículos B (↓)"),
            (DARK_GREY, "Detenidos"),
            (ZONE_D[:3], "Zona D"),
            (ZONE_R[:3], "Zona R"),
            (ZONE_E[:3], "Zona E"),
        ]

        for i, (color, text) in enumerate(legend_items):
            item_y = y + i * 18
            pygame.draw.rect(self.screen, color, (x + 10, item_y, 12, 12))
            pygame.draw.rect(self.screen, BLACK, (x + 10, item_y, 12, 12), 1)
            text_surf = self.small_font.render(text, True, BLACK)
            self.screen.blit(text_surf, (x + 28, item_y - 1))

    def draw(self):
        """Renderiza toda la escena."""
        self.screen.fill(WHITE)
        self._draw_road_infrastructure()
        self._draw_zones()
        self._draw_vehicles()
        self._draw_traffic_lights()
        self._draw_hud()
        pygame.display.flip()

    def run(self):
        """Loop principal de la interfaz."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_UP:
                        self.speedup = min(8, self.speedup + 1)
                    elif event.key == pygame.K_DOWN:
                        self.speedup = max(1, self.speedup - 1)
                    elif event.key == pygame.K_RIGHT:
                        # Aumentar spawn rate
                        self.sim.intersection.lane_A.spawn_rate = min(
                            0.20, self.sim.intersection.lane_A.spawn_rate + 0.01
                        )
                        self.sim.intersection.lane_B.spawn_rate = min(
                            0.20, self.sim.intersection.lane_B.spawn_rate + 0.01
                        )
                    elif event.key == pygame.K_LEFT:
                        # Disminuir spawn rate
                        self.sim.intersection.lane_A.spawn_rate = max(
                            0.01, self.sim.intersection.lane_A.spawn_rate - 0.01
                        )
                        self.sim.intersection.lane_B.spawn_rate = max(
                            0.01, self.sim.intersection.lane_B.spawn_rate - 0.01
                        )
                    elif event.key == pygame.K_z:
                        self.show_zones = not self.show_zones
                    elif event.key == pygame.K_s:
                        self.show_stats = not self.show_stats
                    elif event.key == pygame.K_r:
                        self.sim.reset()

            # Ejecutar simulación si no está pausada
            if not self.paused:
                for _ in range(self.speedup):
                    if not self.sim.step():
                        break

            self.draw()
            self.clock.tick(30)  # 30 FPS

        pygame.quit()
        sys.exit()
