# semaforos/gui.py
"""
Interfaz gráfica final para la simulación usando pygame.

Características:
- Zonas D, R, E dibujadas como bandas del tamaño del cruce.
- Flechas orientadas correctamente: A (→), B (↓).
- Separación visual mínima entre vehículos: 5 px.
- Vehículos visibles mientras cruzan y hasta salir fuera de pantalla.
- Sólo 2 semáforos: A (izquierda) y B (arriba).
- No borra vehículos; la limpieza la hace Lane cuando corresponde.
- Controles: SPACE pausa/reanuda | UP/DOWN velocidad | LEFT/RIGHT spawn rate | ESC salir
"""

import pygame
import sys
from .simulation import Simulation
from .lane import Lane

# Colores
WHITE = (250, 250, 250)
BLACK = (10, 10, 10)
ROAD = (200, 200, 200)
LANE_MARK = (230, 230, 230)
RED = (220, 50, 50)
GREEN = (50, 200, 80)
YELLOW = (240, 200, 60)
BLUE = (60, 110, 200)
MAGENTA = (170, 70, 170)
DARK_GREY = (120, 120, 120)

# Zonas (RGBA) - semitransparente
ZONE_D = (180, 200, 255, 110)  # azul claro
ZONE_R = (200, 255, 200, 110)  # verde claro
ZONE_E = (255, 200, 200, 110)  # rojo claro


class GUI:
    def __init__(self, sim: Simulation, width: int = 1000, height: int = 700):
        pygame.init()
        self.sim = sim
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Semáforos Auto-organizantes - Simulación")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.small_font = pygame.font.SysFont("Arial", 14)

        # layout
        self.stop_x = width // 2
        self.stop_y = height // 2
        self.road_half_width = 80

        # visual vehicle sizes and spacing
        self.vehicle_w = 28
        self.vehicle_h = 18
        self.min_pixel_gap = 5  # separación visual mínima, como pediste

        # controls
        self.paused = False
        self.speedup = 1  # pasos de simulación por frame (1 por defecto)

    # ---------- utilidades de mapeo ----------
    def _map_horizontal_pos_to_pixel(self, position: float, lane: Lane) -> int:
        """
        position >= 0 : aproximación desde la izquierda hacia stop_x
        position < 0  : ya cruzó, se mueve hacia la derecha
        """
        if position >= 0:
            frac = min(position / max(1.0, lane.lane_length), 1.0)
            x = int(self.stop_x - frac * (self.stop_x - 100))
        else:
            frac = min((-position) / max(1.0, lane.lane_length), 1.0)
            x = int(self.stop_x + frac * (self.width - self.stop_x - 100))
        return x

    def _map_vertical_pos_to_pixel(self, position: float, lane: Lane) -> int:
        """
        position >= 0 : aproximación desde arriba hacia stop_y
        position < 0  : ya cruzó, se mueve hacia abajo
        """
        if position >= 0:
            frac = min(position / max(1.0, lane.lane_length), 1.0)
            y = int(self.stop_y - frac * (self.stop_y - 100))
        else:
            frac = min((-position) / max(1.0, lane.lane_length), 1.0)
            y = int(self.stop_y + frac * (self.height - self.stop_y - 100))
        return y

    # ---------- dibujo de carretera y marcas ----------
    def _draw_road(self):
        # carretera horizontal y vertical (cruce central)
        pygame.draw.rect(
            self.screen,
            ROAD,
            (
                0,
                self.stop_y - self.road_half_width,
                self.width,
                self.road_half_width * 2,
            ),
        )
        pygame.draw.rect(
            self.screen,
            ROAD,
            (
                self.stop_x - self.road_half_width,
                0,
                self.road_half_width * 2,
                self.height,
            ),
        )

        # marcas punteadas horizontales (definen el cruce)
        dash_w = 20
        gap = 14
        y_top = int(self.stop_y - self.road_half_width / 2)
        y_bottom = int(self.stop_y + self.road_half_width / 2 - 6)
        x = 20
        while x < self.width:
            pygame.draw.rect(self.screen, LANE_MARK, (x, y_top - 6, dash_w, 6))
            pygame.draw.rect(self.screen, LANE_MARK, (x, y_bottom, dash_w, 6))
            x += dash_w + gap

        # marcas punteadas verticales
        y = 20
        x_left = int(self.stop_x - self.road_half_width / 2)
        x_right = int(self.stop_x + self.road_half_width / 2 - 6)
        while y < self.height:
            pygame.draw.rect(self.screen, LANE_MARK, (x_left - 6, y, 6, dash_w))
            pygame.draw.rect(self.screen, LANE_MARK, (x_right, y, 6, dash_w))
            y += dash_w + gap

        # líneas de detención (más sutiles)
        pygame.draw.line(
            self.screen,
            BLACK,
            (self.stop_x - 6, self.stop_y - self.road_half_width),
            (self.stop_x - 6, self.stop_y + self.road_half_width),
            3,
        )
        pygame.draw.line(
            self.screen,
            BLACK,
            (self.stop_x + 6, self.stop_y - self.road_half_width),
            (self.stop_x + 6, self.stop_y + self.road_half_width),
            3,
        )
        pygame.draw.line(
            self.screen,
            BLACK,
            (self.stop_x - self.road_half_width, self.stop_y - 6),
            (self.stop_x + self.road_half_width, self.stop_y - 6),
            3,
        )
        pygame.draw.line(
            self.screen,
            BLACK,
            (self.stop_x - self.road_half_width, self.stop_y + 6),
            (self.stop_x + self.road_half_width, self.stop_y + 6),
            3,
        )

    # ---------- dibujo de zonas D / R / E ----------
    def _draw_zones(self):
        inter = self.sim.intersection
        la = inter.lane_A
        lb = inter.lane_B
        d = inter.d
        r = inter.r
        e = inter.e

        # helpers para convertir dist a píxeles (en la aproximación)
        def to_px_h(dist, lane):
            frac = min(dist / max(1.0, lane.lane_length), 1.0)
            return int(frac * (self.stop_x - 100))

        def to_px_v(dist, lane):
            frac = min(dist / max(1.0, lane.lane_length), 1.0)
            return int(frac * (self.stop_y - 100))

        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Horizontal (izquierda -> stop_x)
        px_d = to_px_h(d, la)
        px_r = to_px_h(r, la)
        px_e = to_px_h(e, la)
        # Dibujar D (más lejana), R (intermedia) y E (más cercana)
        rect_d = (
            self.stop_x - px_d - self.road_half_width,
            self.stop_y - self.road_half_width,
            px_d,
            self.road_half_width * 2,
        )
        rect_r = (
            self.stop_x - px_r - self.road_half_width,
            self.stop_y - self.road_half_width,
            px_r,
            self.road_half_width * 2,
        )
        rect_e = (
            self.stop_x - px_e - self.road_half_width,
            self.stop_y - self.road_half_width,
            px_e,
            self.road_half_width * 2,
        )
        if rect_d[2] > 0:
            surf.fill(ZONE_D, rect_d)
        if rect_r[2] > 0:
            surf.fill(ZONE_R, rect_r)
        if rect_e[2] > 0:
            surf.fill(ZONE_E, rect_e)

        # Vertical (arriba -> stop_y)
        py_d = to_px_v(d, lb)
        py_r = to_px_v(r, lb)
        py_e = to_px_v(e, lb)
        rect_dv = (
            self.stop_x - self.road_half_width,
            self.stop_y - py_d - self.road_half_width,
            self.road_half_width * 2,
            py_d,
        )
        rect_rv = (
            self.stop_x - self.road_half_width,
            self.stop_y - py_r - self.road_half_width,
            self.road_half_width * 2,
            py_r,
        )
        rect_ev = (
            self.stop_x - self.road_half_width,
            self.stop_y - py_e - self.road_half_width,
            self.road_half_width * 2,
            py_e,
        )
        if rect_dv[3] > 0:
            surf.fill(ZONE_D, rect_dv)
        if rect_rv[3] > 0:
            surf.fill(ZONE_R, rect_rv)
        if rect_ev[3] > 0:
            surf.fill(ZONE_E, rect_ev)

        self.screen.blit(surf, (0, 0))

    # ---------- dibujo de vehículos ----------
    def _draw_vehicles(self):
        inter = self.sim.intersection
        la = inter.lane_A
        lb = inter.lane_B

        # --- Lane A (horizontal, → ) ---
        # mantener la lista completa para poder dibujar vehículos que ya cruzaron (position < 0)
        # pero aplicaremos separación visual mínima solo en la aproximación (position >= 0),
        # para que en la cola se vean ordenados y separados.
        approach_a = sorted(
            [v for v in la.vehicles if v.position >= 0], key=lambda v: v.position
        )
        # mapear a pixeles
        pixels = []
        for v in approach_a:
            x = self._map_horizontal_pos_to_pixel(v.position, la)
            pixels.append((v, x))
        # aplicar separación visual mínima (de adelante hacia atrás)
        adjusted = []
        for i, (v, x) in enumerate(pixels):
            if i == 0:
                adjusted.append((v, x))
            else:
                prev_x = adjusted[-1][1]
                min_x = prev_x - (self.vehicle_w + self.min_pixel_gap)
                if x > min_x:
                    x = min_x
                adjusted.append((v, x))

        # dibujar la aproximación A
        y_a = self.stop_y - int(self.road_half_width / 3)
        for v, x in adjusted:
            color = BLUE if not v.stopped else DARK_GREY
            rect = pygame.Rect(
                x - self.vehicle_w // 2,
                y_a - self.vehicle_h // 2,
                self.vehicle_w,
                self.vehicle_h,
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            # flecha a la derecha (→)
            ax = x + self.vehicle_w // 2 - 4
            ay = y_a
            pygame.draw.polygon(
                self.screen, BLACK, [(ax, ay), (ax + 8, ay - 6), (ax + 8, ay + 6)]
            )

        # dibujar vehículos que ya cruzaron (position < 0) para que se vean en la parte derecha hasta salir
        beyond_a = sorted(
            [v for v in la.vehicles if v.position < 0], key=lambda v: v.position
        )  # más negativo -> más lejos
        for v in beyond_a:
            x = self._map_horizontal_pos_to_pixel(v.position, la)
            color = BLUE if not v.stopped else DARK_GREY
            rect = pygame.Rect(
                x - self.vehicle_w // 2,
                y_a - self.vehicle_h // 2,
                self.vehicle_w,
                self.vehicle_h,
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            ax = x + self.vehicle_w // 2 - 4
            ay = y_a
            pygame.draw.polygon(
                self.screen, BLACK, [(ax, ay), (ax + 8, ay - 6), (ax + 8, ay + 6)]
            )

        # --- Lane B (vertical, ↓) ---
        approach_b = sorted(
            [v for v in lb.vehicles if v.position >= 0], key=lambda v: v.position
        )
        pixels_b = []
        for v in approach_b:
            y = self._map_vertical_pos_to_pixel(v.position, lb)
            pixels_b.append((v, y))
        adjusted_b = []
        for i, (v, y) in enumerate(pixels_b):
            if i == 0:
                adjusted_b.append((v, y))
            else:
                prev_y = adjusted_b[-1][1]
                min_y = prev_y - (self.vehicle_h + self.min_pixel_gap)
                if y > min_y:
                    y = min_y
                adjusted_b.append((v, y))

        x_b = self.stop_x + int(self.road_half_width / 3)
        for v, y in adjusted_b:
            color = MAGENTA if not v.stopped else DARK_GREY
            rect = pygame.Rect(
                x_b - self.vehicle_w // 2,
                y - self.vehicle_h // 2,
                self.vehicle_w,
                self.vehicle_h,
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            # flecha hacia abajo (↓)
            ax = x_b
            ay = y + self.vehicle_h // 2 - 4
            pygame.draw.polygon(
                self.screen, BLACK, [(ax, ay), (ax - 6, ay + 8), (ax + 6, ay + 8)]
            )

        # vehículos que ya cruzaron verticalmente (position < 0) -> se muestran hacia abajo
        beyond_b = sorted(
            [v for v in lb.vehicles if v.position < 0], key=lambda v: v.position
        )
        for v in beyond_b:
            y = self._map_vertical_pos_to_pixel(v.position, lb)
            color = MAGENTA if not v.stopped else DARK_GREY
            rect = pygame.Rect(
                x_b - self.vehicle_w // 2,
                y - self.vehicle_h // 2,
                self.vehicle_w,
                self.vehicle_h,
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            ax = x_b
            ay = y + self.vehicle_h // 2 - 4
            pygame.draw.polygon(
                self.screen, BLACK, [(ax, ay), (ax - 6, ay + 8), (ax + 6, ay + 8)]
            )

    # ---------- dibujo de semáforos ----------
    def _draw_traffic_light_panel(self, light, px, py, panel_w=34, panel_h=90):
        pygame.draw.rect(
            self.screen, (40, 40, 40), (px, py, panel_w, panel_h), border_radius=6
        )
        for i, col in enumerate([RED, YELLOW, GREEN]):
            r = 10
            cy = py + 18 + i * 28
            on = (
                (light.state == "red" and i == 0)
                or (light.state == "yellow" and i == 1)
                or (light.state == "green" and i == 2)
            )
            draw_col = col if on else (60, 60, 60)
            pygame.draw.circle(self.screen, draw_col, (px + panel_w // 2, cy), r)

    def _draw_traffic_lights(self):
        inter = self.sim.intersection
        la = inter.light_A
        lb = inter.light_B
        # Solo 2 semáforos: A (left) y B (top)
        px_a = self.stop_x - self.road_half_width - 60
        py_a = self.stop_y - 30
        self._draw_traffic_light_panel(la, px_a, py_a)
        self.screen.blit(
            self.small_font.render(f"A:{la.state} g={la.green_time}", True, BLACK),
            (px_a - 6, py_a + 96),
        )

        px_b = self.stop_x - 17
        py_b = self.stop_y - self.road_half_width - 120
        self._draw_traffic_light_panel(lb, px_b, py_b)
        self.screen.blit(
            self.small_font.render(f"B:{lb.state} g={lb.green_time}", True, BLACK),
            (px_b - 6, py_b + 96),
        )

    # ---------- HUD ----------
    def _draw_hud(self):
        t = self.sim.get_time()
        la = self.sim.intersection.lane_A
        lb = self.sim.intersection.lane_B
        st = self.sim.intersection.get_state()
        lines = [
            f"t={t}  |  pause SPACE  |  speed +/-  |  spawn +/- LEFT/RIGHT",
            f"spawnA={la.spawn_rate:.2f}  spawnB={lb.spawn_rate:.2f}   |   cA={st['counter_A']}  cB={st['counter_B']}  both_red={st['both_red']}",
        ]
        y = 8
        for ln in lines:
            surf = self.font.render(ln, True, BLACK)
            self.screen.blit(surf, (12, y))
            y += 22

        # leyenda compacta
        legend = [
            (BLUE, "A vehicles (→)"),
            (MAGENTA, "B vehicles (↓)"),
            (DARK_GREY, "stopped"),
        ]
        x = self.width - 260
        y = 12
        for col, text in legend:
            pygame.draw.rect(self.screen, col, (x, y, 18, 12))
            self.screen.blit(self.small_font.render(text, True, BLACK), (x + 26, y - 2))
            y += 20

    # ---------- render completo ----------
    def draw(self):
        self.screen.fill(WHITE)
        self._draw_road()
        # dibujar bandas D/R/E
        self._draw_zones()
        # dibujar vehículos (no borra nada)
        self._draw_vehicles()
        # semáforos y HUD
        self._draw_traffic_lights()
        self._draw_hud()
        pygame.display.flip()

    # ---------- loop principal ----------
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_UP:
                        self.speedup = min(6, self.speedup + 1)
                    elif event.key == pygame.K_DOWN:
                        self.speedup = max(1, self.speedup - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.sim.intersection.lane_A.spawn_rate = min(
                            0.9, self.sim.intersection.lane_A.spawn_rate + 0.02
                        )
                        self.sim.intersection.lane_B.spawn_rate = min(
                            0.9, self.sim.intersection.lane_B.spawn_rate + 0.02
                        )
                    elif event.key == pygame.K_LEFT:
                        self.sim.intersection.lane_A.spawn_rate = max(
                            0.0, self.sim.intersection.lane_A.spawn_rate - 0.02
                        )
                        self.sim.intersection.lane_B.spawn_rate = max(
                            0.0, self.sim.intersection.lane_B.spawn_rate - 0.02
                        )
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            if not self.paused:
                for _ in range(self.speedup):
                    self.sim.step()

            self.draw()
            self.clock.tick(20)  # framerate - moderado para seguir visualmente

        pygame.quit()
        sys.exit()
