import pygame
import sys
import math
from .simulation import Simulation
from .lane import Lane

# Colores mejorados
WHITE = (250, 250, 250)
BLACK = (10, 10, 10)
ROAD = (200, 200, 200)
LANE_MARK = (255, 255, 255)
RED = (220, 50, 50)
GREEN = (50, 200, 80)
YELLOW = (240, 200, 60)
BLUE = (60, 110, 200)
MAGENTA = (170, 70, 170)
DARK_GREY = (120, 120, 120)
LIGHT_GREY = (180, 180, 180)
ORANGE = (255, 140, 0)

# Zonas con mejor transparencia
ZONE_D = (100, 150, 255, 80)
ZONE_R = (255, 200, 100, 80)
ZONE_E = (255, 100, 100, 80)

# Colores para indicadores de tráfico
TRAFFIC_LOW = (100, 200, 100)
TRAFFIC_MEDIUM = (200, 200, 100)
TRAFFIC_HIGH = (200, 100, 100)


class GUI:
    def __init__(self, sim: Simulation, width: int = 1200, height: int = 800):
        pygame.init()
        self.sim = sim
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Semáforos Auto-organizantes - Simulación Mejorada")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 12)
        self.tiny_font = pygame.font.SysFont("Arial", 10)

        # Coordenadas del cruce
        self.center_x = width // 2
        self.center_y = height // 2
        self.road_width = 160
        self.lane_width = 40
        self.intersection_size = 120

        # Líneas de parada
        self.stop_line_A_x = self.center_x - self.intersection_size // 2
        self.stop_line_B_y = self.center_y - self.intersection_size // 2

        # Tamaños de vehículos mejorados
        self.vehicle_w = 30
        self.vehicle_h = 18
        self.min_pixel_gap = 8

        # Controles y visualización
        self.paused = False
        self.speedup = 1
        self.show_zones = True
        self.show_stats = True
        self.show_debug = False
        self.show_traffic_patterns = True

    def _map_position_A_to_pixel(self, position: float, lane: Lane) -> int:
        """Mapea posición del carril A a coordenada X con mejor precisión."""
        if position >= 0:
            frac = min(position / max(1.0, lane.lane_length), 1.0)
            x = int(self.stop_line_A_x - frac * (self.stop_line_A_x - 50))
        else:
            frac = min((-position) / max(1.0, lane.lane_length), 1.0)
            x = int(
                self.stop_line_A_x
                + self.intersection_size
                + frac * (self.width - self.stop_line_A_x - self.intersection_size - 50)
            )
        return x

    def _map_position_B_to_pixel(self, position: float, lane: Lane) -> int:
        """Mapea posición del carril B a coordenada Y con mejor precisión."""
        if position >= 0:
            frac = min(position / max(1.0, lane.lane_length), 1.0)
            y = int(self.stop_line_B_y - frac * (self.stop_line_B_y - 50))
        else:
            frac = min((-position) / max(1.0, lane.lane_length), 1.0)
            y = int(
                self.stop_line_B_y
                + self.intersection_size
                + frac
                * (self.height - self.stop_line_B_y - self.intersection_size - 50)
            )
        return y

    def _draw_road_infrastructure(self):
        """Dibuja la infraestructura vial mejorada."""
        # Carreteras con bordes más definidos
        # Horizontal
        pygame.draw.rect(
            self.screen,
            ROAD,
            (0, self.center_y - self.road_width // 2, self.width, self.road_width),
        )
        pygame.draw.rect(
            self.screen,
            DARK_GREY,
            (0, self.center_y - self.road_width // 2, self.width, 3),
        )
        pygame.draw.rect(
            self.screen,
            DARK_GREY,
            (0, self.center_y + self.road_width // 2 - 3, self.width, 3),
        )

        # Vertical
        pygame.draw.rect(
            self.screen,
            ROAD,
            (self.center_x - self.road_width // 2, 0, self.road_width, self.height),
        )
        pygame.draw.rect(
            self.screen,
            DARK_GREY,
            (self.center_x - self.road_width // 2, 0, 3, self.height),
        )
        pygame.draw.rect(
            self.screen,
            DARK_GREY,
            (self.center_x + self.road_width // 2 - 3, 0, 3, self.height),
        )

        # Área del cruce resaltada
        intersection_rect = (
            self.center_x - self.intersection_size // 2,
            self.center_y - self.intersection_size // 2,
            self.intersection_size,
            self.intersection_size,
        )
        pygame.draw.rect(self.screen, LIGHT_GREY, intersection_rect)

        # Líneas punteadas del cruce
        self._draw_intersection_boundaries()
        self._draw_lane_dividers()

    def _draw_intersection_boundaries(self):
        """Dibuja líneas punteadas que definen el cruce."""
        dash_w, gap = 20, 12

        # Líneas horizontales
        y_top = self.center_y - self.intersection_size // 2
        y_bottom = self.center_y + self.intersection_size // 2

        for y in [y_top, y_bottom]:
            x = 20
            while x < self.width:
                if not (
                    self.center_x - self.intersection_size // 2
                    <= x
                    <= self.center_x + self.intersection_size // 2
                ):
                    pygame.draw.rect(self.screen, LANE_MARK, (x, y - 3, dash_w, 6))
                x += dash_w + gap

        # Líneas verticales
        x_left = self.center_x - self.intersection_size // 2
        x_right = self.center_x + self.intersection_size // 2

        for x in [x_left, x_right]:
            y = 20
            while y < self.height:
                if not (
                    self.center_y - self.intersection_size // 2
                    <= y
                    <= self.center_y + self.intersection_size // 2
                ):
                    pygame.draw.rect(self.screen, LANE_MARK, (x - 3, y, 6, dash_w))
                y += dash_w + gap

    def _draw_lane_dividers(self):
        """Dibuja líneas divisorias."""
        pygame.draw.line(
            self.screen, LANE_MARK, (0, self.center_y), (self.width, self.center_y), 2
        )
        pygame.draw.line(
            self.screen, LANE_MARK, (self.center_x, 0), (self.center_x, self.height), 2
        )

    def _draw_zones(self):
        """Dibuja zonas D, R, E con mejor visualización."""
        if not self.show_zones:
            return

        inter = self.sim.intersection
        d, r, e = inter.d, inter.r, inter.e

        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        def dist_to_pixels_h(dist):
            return int((dist / inter.lane_A.lane_length) * (self.stop_line_A_x - 50))

        def dist_to_pixels_v(dist):
            return int((dist / inter.lane_B.lane_length) * (self.stop_line_B_y - 50))

        # Zonas para carril A
        px_d = dist_to_pixels_h(d)
        px_r = dist_to_pixels_h(r)
        px_e = dist_to_pixels_h(e)

        if px_d > 0:
            zone_d_rect = (
                self.stop_line_A_x - px_d,
                self.center_y - self.lane_width,
                px_d,
                self.lane_width * 2,
            )
            surf.fill(ZONE_D, zone_d_rect)

        if px_r > 0:
            zone_r_rect = (
                self.stop_line_A_x - px_r,
                self.center_y - self.lane_width,
                px_r,
                self.lane_width * 2,
            )
            surf.fill(ZONE_R, zone_r_rect)

        if px_e > 0:
            zone_e_rect = (
                self.stop_line_A_x + self.intersection_size,
                self.center_y - self.lane_width,
                px_e,
                self.lane_width * 2,
            )
            surf.fill(ZONE_E, zone_e_rect)

        # Zonas para carril B
        py_d = dist_to_pixels_v(d)
        py_r = dist_to_pixels_v(r)
        py_e = dist_to_pixels_v(e)

        if py_d > 0:
            zone_d_rect = (
                self.center_x - self.lane_width,
                self.stop_line_B_y - py_d,
                self.lane_width * 2,
                py_d,
            )
            surf.fill(ZONE_D, zone_d_rect)

        if py_r > 0:
            zone_r_rect = (
                self.center_x - self.lane_width,
                self.stop_line_B_y - py_r,
                self.lane_width * 2,
                py_r,
            )
            surf.fill(ZONE_R, zone_r_rect)

        if py_e > 0:
            zone_e_rect = (
                self.center_x - self.lane_width,
                self.stop_line_B_y + self.intersection_size,
                self.lane_width * 2,
                py_e,
            )
            surf.fill(ZONE_E, zone_e_rect)

        self.screen.blit(surf, (0, 0))
        self._draw_zone_labels()

    def _draw_zone_labels(self):
        """Dibuja etiquetas de las zonas."""
        label_y = self.center_y - self.lane_width - 25

        # Etiquetas carril A
        d_label = self.small_font.render("ZONA D", True, BLACK)
        self.screen.blit(d_label, (self.stop_line_A_x - 100, label_y))

        r_label = self.small_font.render("ZONA R", True, BLACK)
        self.screen.blit(r_label, (self.stop_line_A_x - 35, label_y))

        e_label = self.small_font.render("ZONA E", True, BLACK)
        self.screen.blit(
            e_label, (self.stop_line_A_x + self.intersection_size + 10, label_y)
        )

        # Etiquetas carril B
        label_x = self.center_x - self.lane_width - 60

        d_label = self.small_font.render("ZONA D", True, BLACK)
        self.screen.blit(d_label, (label_x, self.stop_line_B_y - 100))

        r_label = self.small_font.render("ZONA R", True, BLACK)
        self.screen.blit(r_label, (label_x, self.stop_line_B_y - 35))

        e_label = self.small_font.render("ZONA E", True, BLACK)
        self.screen.blit(
            e_label, (label_x, self.stop_line_B_y + self.intersection_size + 10)
        )

    def _draw_traffic_patterns(self):
        """Dibuja indicadores de patrones de tráfico dinámicos."""
        if not self.show_traffic_patterns:
            return

        stats = self.sim.get_statistics()
        traffic_A = stats["lane_A"]["traffic_info"]
        traffic_B = stats["lane_B"]["traffic_info"]

        # Indicador para carril A
        rate_A = traffic_A["current_spawn_rate"]
        color_A = self._get_traffic_color(rate_A)

        indicator_rect_A = pygame.Rect(50, self.center_y - 60, 80, 20)
        pygame.draw.rect(self.screen, color_A, indicator_rect_A)
        pygame.draw.rect(self.screen, BLACK, indicator_rect_A, 2)

        rate_text = self.tiny_font.render(f"Tráfico A: {rate_A:.3f}", True, BLACK)
        self.screen.blit(rate_text, (52, self.center_y - 58))

        # Indicador para carril B
        rate_B = traffic_B["current_spawn_rate"]
        color_B = self._get_traffic_color(rate_B)

        indicator_rect_B = pygame.Rect(self.center_x - 60, 50, 20, 80)
        pygame.draw.rect(self.screen, color_B, indicator_rect_B)
        pygame.draw.rect(self.screen, BLACK, indicator_rect_B, 2)

        # Texto rotado para carril B
        rate_text_B = self.tiny_font.render(f"Tráfico B: {rate_B:.3f}", True, BLACK)
        # Rotar el texto 90 grados
        rotated_text = pygame.transform.rotate(rate_text_B, 90)
        self.screen.blit(rotated_text, (self.center_x - 58, 52))

    def _get_traffic_color(self, rate: float):
        """Obtiene color basado en la tasa de tráfico."""
        if rate < 0.03:
            return TRAFFIC_LOW
        elif rate < 0.08:
            return TRAFFIC_MEDIUM
        else:
            return TRAFFIC_HIGH

    def _draw_vehicles(self):
        """Dibuja vehículos con mejor separación visual."""
        self._draw_lane_A_vehicles()
        self._draw_lane_B_vehicles()

    def _draw_lane_A_vehicles(self):
        """Dibuja vehículos del carril A con posicionamiento directo y natural - SIMPLIFICADO."""
        lane_a = self.sim.intersection.lane_A
        if not lane_a.vehicles:
            return

        y_position = self.center_y - self.lane_width // 2

        # NUEVO: Dibujar todos los vehículos directamente sin agrupación artificial
        for vehicle in lane_a.vehicles:
            x = self._map_position_A_to_pixel(vehicle.position, lane_a)
            self._draw_vehicle_enhanced(vehicle, x, y_position, True)

    def _draw_lane_B_vehicles(self):
        """Dibuja vehículos del carril B con posicionamiento directo y natural - SIMPLIFICADO."""
        lane_b = self.sim.intersection.lane_B
        if not lane_b.vehicles:
            return

        x_position = self.center_x + self.lane_width // 2

        # NUEVO: Dibujar todos los vehículos directamente sin agrupación artificial
        for vehicle in lane_b.vehicles:
            y = self._map_position_B_to_pixel(vehicle.position, lane_b)
            self._draw_vehicle_enhanced(vehicle, x_position, y, False)

    def _draw_vehicle_enhanced(self, vehicle, x, y, is_horizontal):
        """Dibuja un vehículo con mejor aspecto visual."""
        # Color según estado y carril
        if is_horizontal:
            base_color = BLUE
        else:
            base_color = MAGENTA

        # Gradiente de color según velocidad
        speed_factor = min(1.0, vehicle.speed / self.sim.intersection.lane_A.max_speed)
        if vehicle.stopped:
            color = DARK_GREY
        else:
            # Interpolar color basado en velocidad
            r = int(base_color[0] * (0.7 + 0.3 * speed_factor))
            g = int(base_color[1] * (0.7 + 0.3 * speed_factor))
            b = int(base_color[2] * (0.7 + 0.3 * speed_factor))
            color = (r, g, b)

        # Rectángulo principal del vehículo
        rect = pygame.Rect(
            x - self.vehicle_w // 2,
            y - self.vehicle_h // 2,
            self.vehicle_w,
            self.vehicle_h,
        )
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=6)

        # Ventanas del vehículo
        window_color = (200, 230, 255) if not vehicle.stopped else (150, 150, 150)
        window_rect = pygame.Rect(
            x - self.vehicle_w // 2 + 4,
            y - self.vehicle_h // 2 + 3,
            self.vehicle_w - 8,
            self.vehicle_h - 6,
        )
        pygame.draw.rect(self.screen, window_color, window_rect, border_radius=3)

        # Flecha direccional mejorada
        arrow_color = WHITE if not vehicle.stopped else LIGHT_GREY
        if is_horizontal:
            arrow_points = [
                (x + self.vehicle_w // 2 - 10, y),
                (x + self.vehicle_w // 2 - 4, y - 6),
                (x + self.vehicle_w // 2 - 4, y + 6),
            ]
        else:
            arrow_points = [
                (x, y + self.vehicle_h // 2 - 10),
                (x - 6, y + self.vehicle_h // 2 - 4),
                (x + 6, y + self.vehicle_h // 2 - 4),
            ]
        pygame.draw.polygon(self.screen, arrow_color, arrow_points)

        # ID del vehículo (opcional, para debug)
        if self.show_debug:
            id_text = self.tiny_font.render(str(vehicle.id), True, WHITE)
            self.screen.blit(id_text, (x - 6, y - 6))

    def _draw_traffic_lights(self):
        """Dibuja semáforos con mejor diseño."""
        inter = self.sim.intersection

        # Posiciones de los semáforos
        light_a_x = self.stop_line_A_x - 70
        light_a_y = self.center_y - 50
        self._draw_traffic_light_enhanced(inter.light_A, light_a_x, light_a_y, "A")

        light_b_x = self.center_x - 25
        light_b_y = self.stop_line_B_y - 110
        self._draw_traffic_light_enhanced(inter.light_B, light_b_x, light_b_y, "B")

    def _draw_traffic_light_enhanced(self, light, x, y, name):
        """Dibuja un semáforo con diseño mejorado."""
        width, height = 40, 100

        # Sombra del semáforo
        shadow_rect = pygame.Rect(x + 3, y + 3, width, height)
        pygame.draw.rect(self.screen, (60, 60, 60), shadow_rect, border_radius=8)

        # Fondo del semáforo
        main_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (40, 40, 40), main_rect, border_radius=8)
        pygame.draw.rect(self.screen, BLACK, main_rect, 3, border_radius=8)

        # Luces
        colors = [RED, YELLOW, GREEN]
        states = ["red", "yellow", "green"]

        for i, (color, state) in enumerate(zip(colors, states)):
            center_y = y + 20 + i * 28
            radius = 12

            is_on = light.state == state

            if is_on:
                # Efecto de brillo para la luz activa
                glow_radius = radius + 4
                glow_color = (*color, 100)
                glow_surf = pygame.Surface(
                    (glow_radius * 2, glow_radius * 2), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    glow_surf, glow_color, (glow_radius, glow_radius), glow_radius
                )
                self.screen.blit(
                    glow_surf, (x + width // 2 - glow_radius, center_y - glow_radius)
                )

                draw_color = color
            else:
                draw_color = (color[0] // 4, color[1] // 4, color[2] // 4)

            pygame.draw.circle(
                self.screen, draw_color, (x + width // 2, center_y), radius
            )
            pygame.draw.circle(
                self.screen, BLACK, (x + width // 2, center_y), radius, 2
            )

        # Información del semáforo
        info = f"{name}: {light.state.upper()}"
        time_info = f"t={light.green_time}s" if light.state == "green" else ""

        text = self.small_font.render(info, True, BLACK)
        self.screen.blit(text, (x - 5, y + height + 5))

        if time_info:
            time_text = self.tiny_font.render(time_info, True, DARK_GREY)
            self.screen.blit(time_text, (x - 5, y + height + 22))

    def _draw_hud(self):
        """Dibuja HUD con información mejorada."""
        stats = self.sim.get_statistics()
        inter_state = stats["intersection_state"]

        # HUD principal
        info_lines = [
            f"Tiempo: {stats['time']} | {'PAUSADO' if self.paused else f'Velocidad: {self.speedup}x'}",
            f"Eficiencia Sistema: {stats['system_efficiency']:.1f}% | Tiempo Espera Prom: {stats['avg_wait_time']:.1f}",
            f"Vehículos: Total={stats['total_spawned']} | Completados={stats['total_completed']}",
            f"Contadores: A={inter_state['counter_A']} | B={inter_state['counter_B']} | Cambios: {inter_state['total_changes']}",
        ]

        if inter_state["both_red"]:
            info_lines.append("🚨 EMERGENCIA: Bloqueo cruzado detectado")

        if inter_state["last_change_reason"]:
            info_lines.append(f"Último cambio: {inter_state['last_change_reason']}")

        # Fondo del HUD con transparencia
        hud_height = len(info_lines) * 24 + 20
        hud_surf = pygame.Surface((self.width - 20, hud_height), pygame.SRCALPHA)
        hud_surf.fill((255, 255, 255, 240))
        self.screen.blit(hud_surf, (10, 10))

        hud_rect = pygame.Rect(10, 10, self.width - 20, hud_height)
        pygame.draw.rect(self.screen, BLACK, hud_rect, 2)

        # Texto del HUD
        y = 20
        for line in info_lines:
            color = RED if "EMERGENCIA" in line else BLACK
            text_surf = self.font.render(line, True, color)
            self.screen.blit(text_surf, (20, y))
            y += 24

        # Panel de controles
        self._draw_controls()

        # Paneles adicionales
        if self.show_stats:
            self._draw_stats_panel(stats)

        if self.show_debug:
            self._draw_debug_panel()

    def _draw_controls(self):
        """Dibuja ayuda de controles mejorada."""
        controls = [
            "CONTROLES:",
            "ESPACIO: Pausar/Reanudar",
            "↑/↓: Velocidad simulación",
            "←/→: Patrones de tráfico",
            "Z: Zonas D,R,E on/off",
            "S: Estadísticas on/off",
            "D: Debug info on/off",
            "T: Patrones tráfico on/off",
            "R: Reiniciar simulación",
            "ESC: Salir",
        ]

        y_start = self.height - len(controls) * 18 - 15

        # Fondo de controles
        control_height = len(controls) * 18 + 10
        control_surf = pygame.Surface((200, control_height), pygame.SRCALPHA)
        control_surf.fill((255, 255, 255, 200))
        self.screen.blit(control_surf, (15, y_start - 5))

        control_rect = pygame.Rect(15, y_start - 5, 200, control_height)
        pygame.draw.rect(self.screen, BLACK, control_rect, 1)

        for i, line in enumerate(controls):
            font = self.font if i == 0 else self.small_font
            color = DARK_GREY if i == 0 else BLACK
            text = font.render(line, True, color)
            self.screen.blit(text, (20, y_start + i * 18))

    def _draw_stats_panel(self, stats):
        """Dibuja panel de estadísticas mejorado."""
        inter_state = stats["intersection_state"]
        lane_A_stats = stats["lane_A"]
        lane_B_stats = stats["lane_B"]

        stat_lines = [
            "ESTADÍSTICAS DETALLADAS",
            "",
            "CARRIL A:",
            f"  Vehículos: {inter_state['vehicles_A']} (esperando: {inter_state['waiting_A']})",
            f"  Generados: {lane_A_stats['spawned']} | Completados: {lane_A_stats['completed']}",
            f"  Eficiencia: {lane_A_stats['efficiency']:.1f}%",
            f"  Tasa actual: {lane_A_stats['traffic_info']['current_spawn_rate']:.4f}",
            "",
            "CARRIL B:",
            f"  Vehículos: {inter_state['vehicles_B']} (esperando: {inter_state['waiting_B']})",
            f"  Generados: {lane_B_stats['spawned']} | Completados: {lane_B_stats['completed']}",
            f"  Eficiencia: {lane_B_stats['efficiency']:.1f}%",
            f"  Tasa actual: {lane_B_stats['traffic_info']['current_spawn_rate']:.4f}",
            "",
            "SEMÁFOROS:",
            f"  Tiempo verde A: {inter_state['light_A_gtime']}s",
            f"  Tiempo verde B: {inter_state['light_B_gtime']}s",
            "",
            "PARÁMETROS:",
            f"  d={self.sim.intersection.d} (detección)",
            f"  n={self.sim.intersection.n} (umbral contador)",
            f"  u={self.sim.intersection.u} (tiempo mín verde)",
            f"  m={self.sim.intersection.m} (vehículos cerca máx)",
            f"  r={self.sim.intersection.r} (distancia restricción)",
            f"  e={self.sim.intersection.e} (distancia emergencia)",
        ]

        # Panel en el lado derecho
        panel_width = 320
        panel_height = len([l for l in stat_lines if l != ""]) * 16 + 30
        panel_x = self.width - panel_width - 10
        panel_y = 150

        # Fondo con transparencia
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surf.fill((255, 255, 255, 250))
        self.screen.blit(panel_surf, (panel_x, panel_y))

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)

        # Texto del panel
        y = panel_y + 10
        for line in stat_lines:
            if line == "":
                y += 8
                continue

            if line in [
                "ESTADÍSTICAS DETALLADAS",
                "CARRIL A:",
                "CARRIL B:",
                "SEMÁFOROS:",
                "PARÁMETROS:",
            ]:
                font = self.font
                color = DARK_GREY
            elif line.startswith("  "):
                font = self.small_font
                color = BLACK
            else:
                font = self.small_font
                color = BLACK

            text = font.render(line, True, color)
            self.screen.blit(text, (panel_x + 10, y))
            y += 16

        # Gráfico de rendimiento simple
        if stats["throughput_history"]:
            self._draw_throughput_graph(
                panel_x + 10, y + 10, 280, 60, stats["throughput_history"]
            )

    def _draw_throughput_graph(self, x, y, width, height, data):
        """Dibuja un gráfico simple de rendimiento."""
        if len(data) < 2:
            return

        # Fondo del gráfico
        graph_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, WHITE, graph_rect)
        pygame.draw.rect(self.screen, BLACK, graph_rect, 1)

        # Título
        title = self.small_font.render("Rendimiento (últimos 10 períodos)", True, BLACK)
        self.screen.blit(title, (x, y - 20))

        # Escalar datos
        max_val = max(data) if max(data) > 0 else 1
        min_val = min(data)

        # Dibujar línea
        points = []
        for i, val in enumerate(data):
            px = x + (i / (len(data) - 1)) * width
            py = y + height - ((val - min_val) / max(1, max_val - min_val)) * height
            points.append((px, py))

        if len(points) > 1:
            pygame.draw.lines(self.screen, BLUE, False, points, 2)

        # Valores en los extremos
        if data:
            min_text = self.tiny_font.render(f"{min_val:.1f}", True, BLACK)
            max_text = self.tiny_font.render(f"{max_val:.1f}", True, BLACK)
            self.screen.blit(min_text, (x + 2, y + height - 12))
            self.screen.blit(max_text, (x + 2, y + 2))

    def _draw_debug_panel(self):
        """Dibuja panel de información de debug."""
        debug_info = self.sim.get_debug_info()
        rule_checks = debug_info["rule_checks"]
        spawn_rates = debug_info["current_spawn_rates"]

        debug_lines = [
            "DEBUG INFO:",
            "",
            "CONTEOS DE VEHÍCULOS:",
            f"  Aproximándose A (d={self.sim.intersection.d}): {rule_checks['vehicles_approaching_A']}",
            f"  Aproximándose B (d={self.sim.intersection.d}): {rule_checks['vehicles_approaching_B']}",
            f"  Cerca A (r={self.sim.intersection.r}): {rule_checks['vehicles_close_A']}",
            f"  Cerca B (r={self.sim.intersection.r}): {rule_checks['vehicles_close_B']}",
            "",
            "ESTADO DE REGLAS:",
            f"  Bloqueado después A: {'SÍ' if rule_checks['blocked_after_A'] else 'NO'}",
            f"  Bloqueado después B: {'SÍ' if rule_checks['blocked_after_B'] else 'NO'}",
            f"  Contador A: {rule_checks['counter_A']}",
            f"  Contador B: {rule_checks['counter_B']}",
            f"  Tiempo verde A: {rule_checks['light_A_green_time']}",
            f"  Tiempo verde B: {rule_checks['light_B_green_time']}",
            "",
            "TASAS DE SPAWN:",
            f"  Carril A: {spawn_rates['lane_A']:.6f}",
            f"  Carril B: {spawn_rates['lane_B']:.6f}",
        ]

        # Panel en la esquina inferior derecha
        panel_width = 300
        panel_height = len([l for l in debug_lines if l != ""]) * 14 + 20
        panel_x = self.width - panel_width - 10
        panel_y = self.height - panel_height - 10

        # Fondo
        debug_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        debug_surf.fill((255, 255, 200, 240))  # Fondo amarillento para debug
        self.screen.blit(debug_surf, (panel_x, panel_y))

        debug_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, ORANGE, debug_rect, 2)

        # Texto
        y = panel_y + 10
        for line in debug_lines:
            if line == "":
                y += 6
                continue

            if line.endswith(":"):
                font = self.small_font
                color = ORANGE
            else:
                font = self.tiny_font
                color = BLACK

            text = font.render(line, True, color)
            self.screen.blit(text, (panel_x + 8, y))
            y += 14

    def _draw_legend(self):
        """Dibuja leyenda de colores mejorada."""
        legend_items = [
            (BLUE, "Vehículos A (→)"),
            (MAGENTA, "Vehículos B (↓)"),
            (DARK_GREY, "Vehículos detenidos"),
            (ZONE_D[:3], "Zona D (detección)"),
            (ZONE_R[:3], "Zona R (restricción)"),
            (ZONE_E[:3], "Zona E (emergencia)"),
            (TRAFFIC_HIGH, "Tráfico alto"),
            (TRAFFIC_MEDIUM, "Tráfico medio"),
            (TRAFFIC_LOW, "Tráfico bajo"),
        ]

        legend_x = self.width - 250
        legend_y = self.height - len(legend_items) * 20 - 30

        # Fondo de la leyenda
        legend_surf = pygame.Surface(
            (230, len(legend_items) * 20 + 10), pygame.SRCALPHA
        )
        legend_surf.fill((255, 255, 255, 200))
        self.screen.blit(legend_surf, (legend_x, legend_y))

        legend_rect = pygame.Rect(legend_x, legend_y, 230, len(legend_items) * 20 + 10)
        pygame.draw.rect(self.screen, BLACK, legend_rect, 1)

        for i, (color, text) in enumerate(legend_items):
            item_y = legend_y + 5 + i * 20

            # Cuadro de color
            color_rect = pygame.Rect(legend_x + 8, item_y, 15, 15)
            pygame.draw.rect(self.screen, color, color_rect)
            pygame.draw.rect(self.screen, BLACK, color_rect, 1)

            # Texto
            text_surf = self.small_font.render(text, True, BLACK)
            self.screen.blit(text_surf, (legend_x + 30, item_y))

    def draw(self):
        """Renderiza toda la escena."""
        self.screen.fill(WHITE)
        self._draw_road_infrastructure()
        self._draw_zones()
        self._draw_traffic_patterns()
        self._draw_vehicles()
        self._draw_traffic_lights()
        self._draw_hud()

        if self.show_zones:
            self._draw_legend()

        pygame.display.flip()

    def run(self):
        """Loop principal mejorado de la interfaz."""
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
                        self.speedup = min(10, self.speedup + 1)
                    elif event.key == pygame.K_DOWN:
                        self.speedup = max(1, self.speedup - 1)
                    elif event.key == pygame.K_RIGHT:
                        # Aumentar multiplicadores de pico de tráfico
                        for lane in [
                            self.sim.intersection.lane_A,
                            self.sim.intersection.lane_B,
                        ]:
                            lane.traffic_pattern.peak_multiplier = min(
                                5.0, lane.traffic_pattern.peak_multiplier + 0.2
                            )
                    elif event.key == pygame.K_LEFT:
                        # Disminuir multiplicadores de pico de tráfico
                        for lane in [
                            self.sim.intersection.lane_A,
                            self.sim.intersection.lane_B,
                        ]:
                            lane.traffic_pattern.peak_multiplier = max(
                                1.5, lane.traffic_pattern.peak_multiplier - 0.2
                            )
                    elif event.key == pygame.K_z:
                        self.show_zones = not self.show_zones
                    elif event.key == pygame.K_s:
                        self.show_stats = not self.show_stats
                    elif event.key == pygame.K_d:
                        self.show_debug = not self.show_debug
                    elif event.key == pygame.K_t:
                        self.show_traffic_patterns = not self.show_traffic_patterns
                    elif event.key == pygame.K_r:
                        self.sim.reset()
                        print("Simulación reiniciada")

            # Ejecutar simulación si no está pausada
            if not self.paused:
                for _ in range(self.speedup):
                    if not self.sim.step():
                        break

            self.draw()
            self.clock.tick(60)  # 60 FPS para suavidad

        pygame.quit()
        sys.exit()
