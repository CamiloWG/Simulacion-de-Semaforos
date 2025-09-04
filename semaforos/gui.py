import pygame
import sys
from typing import Tuple
from .simulation import Simulation
from .intersection import Intersection
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
        self.margin = 40
        self.stop_x = width // 2
        self.stop_y = height // 2
        self.road_half_width = 80  # visual half width of the road cross
        # scale: how many pixels represent 1 unit of lane position on the approach side
        self.approach_scale = (
            self.stop_x - 100
        ) / self.sim.intersection.lane_A.lane_length
        self.approach_scale = max(
            0.6 * self.approach_scale, 0.6
        )  # evitar ser muy pequeño

        self.paused = False
        self.speedup = 1  # steps per frame

    # -------------------- Mapping helpers --------------------
    def _map_horizontal_pos_to_pixel(self, position: float, lane: Lane) -> int:
        """Mapea position (>0 acercándose) a coordenada X en píxeles desde la izquierda hacia stop_x.
        Si position < 0 (ya cruzó), se mapea hacia la derecha del stop_x."""
        if position >= 0:
            max_approach = lane.lane_length
            frac = min(position / max_approach, 1.0)
            x = int(self.stop_x - frac * (self.stop_x - 100))
        else:
            # ya cruzó: mapear hacia la derecha línearmente
            frac = min((-position) / lane.lane_length, 1.0)
            x = int(self.stop_x + frac * (self.width - self.stop_x - 100))
        return x

    def _map_vertical_pos_to_pixel(self, position: float, lane: Lane) -> int:
        if position >= 0:
            max_approach = lane.lane_length
            frac = min(position / max_approach, 1.0)
            y = int(self.stop_y - frac * (self.stop_y - 100))
        else:
            frac = min((-position) / lane.lane_length, 1.0)
            y = int(self.stop_y + frac * (self.height - self.stop_y - 100))
        return y

    # -------------------- Drawing primitives --------------------
    def _draw_road(self):
        # horizontal road
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
        # vertical road
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

    def _draw_road(self):
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

        # dashed lane markings (horizontal)
        dash_w = 20
        gap = 14
        y_top = self.stop_y - self.road_half_width / 2
        y_bottom = self.stop_y + self.road_half_width / 2
        x = 20
        while x < self.width:
            pygame.draw.rect(self.screen, LANE_MARK, (x, y_top - 6, dash_w, 6))
            pygame.draw.rect(self.screen, LANE_MARK, (x, y_bottom, dash_w, 6))
            x += dash_w + gap

        # dashed lane markings (vertical)
        y = 20
        x_left = self.stop_x - self.road_half_width / 2
        x_right = self.stop_x + self.road_half_width / 2
        while y < self.height:
            pygame.draw.rect(self.screen, LANE_MARK, (x_left - 6, y, 6, dash_w))
            pygame.draw.rect(self.screen, LANE_MARK, (x_right, y, 6, dash_w))
            y += dash_w + gap

        # stop lines
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

    def _draw_vehicles(self):
        # Lane A: horizontal, approach from left (position >0) towards stop_x
        la = self.sim.intersection.lane_A
        for v in la.vehicles:
            x = self._map_horizontal_pos_to_pixel(v.position, la)
            # put vehicles on upper lane row
            y = self.stop_y - self.road_half_width / 3
            color = BLUE if not v.stopped else DARK_GREY
            rect = pygame.Rect(x - 12, y - 10, 24, 20)
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            # small arrow to indicate direction (right)
            pygame.draw.polygon(
                self.screen, BLACK, [(x + 10, y), (x + 16, y + 6), (x + 10, y + 12)]
            )

        # Lane B: vertical, approach from top towards stop_y
        lb = self.sim.intersection.lane_B
        for v in lb.vehicles:
            x = self.stop_x + self.road_half_width / 3
            y = self._map_vertical_pos_to_pixel(v.position, lb)
            color = MAGENTA if not v.stopped else DARK_GREY
            rect = pygame.Rect(x - 10, y - 12, 20, 24)
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            # arrow downward
            pygame.draw.polygon(
                self.screen, BLACK, [(x, y + 12), (x - 6, y + 18), (x + 6, y + 18)]
            )

    def _draw_traffic_lights(self):
        # A light (left of intersection, for horizontal traffic)
        la = self.sim.intersection.light_A
        panel_w = 34
        panel_h = 90
        px = self.stop_x - self.road_half_width - 60
        py = self.stop_y - panel_h // 2
        pygame.draw.rect(
            self.screen, (40, 40, 40), (px, py, panel_w, panel_h), border_radius=6
        )
        # circles top to bottom: red,yellow,green
        for i, col in enumerate([RED, YELLOW, GREEN]):
            r = 10
            cy = py + 18 + i * 28
            state = "off"
            if la.state == "red" and i == 0:
                state = "on"
            if la.state == "yellow" and i == 1:
                state = "on"
            if la.state == "green" and i == 2:
                state = "on"
            draw_col = col if state == "on" else (60, 60, 60)
            pygame.draw.circle(self.screen, draw_col, (px + panel_w // 2, cy), r)
        # label
        self.screen.blit(
            self.small_font.render(f"A:{la.state} g={la.green_time}", True, WHITE),
            (px - 10, py + panel_h + 4),
        )

        # B light (right of intersection, for vertical traffic)
        lb = self.sim.intersection.light_B
        px2 = self.stop_x + self.road_half_width + 26
        py2 = self.stop_y - panel_h // 2
        pygame.draw.rect(
            self.screen, (40, 40, 40), (px2, py2, panel_w, panel_h), border_radius=6
        )
        for i, col in enumerate([RED, YELLOW, GREEN]):
            r = 10
            cy = py2 + 18 + i * 28
            state = "off"
            if lb.state == "red" and i == 0:
                state = "on"
            if lb.state == "yellow" and i == 1:
                state = "on"
            if lb.state == "green" and i == 2:
                state = "on"
            draw_col = col if state == "on" else (60, 60, 60)
            pygame.draw.circle(self.screen, draw_col, (px2 + panel_w // 2, cy), r)
        self.screen.blit(
            self.small_font.render(f"B:{lb.state} g={lb.green_time}", True, WHITE),
            (px2 - 10, py2 + panel_h + 4),
        )

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

        # legend
        legend = [
            (BLUE, "A vehicles (→)"),
            (MAGENTA, "B vehicles (↓)"),
            (DARK_GREY, "stopped"),
        ]
        x = self.width - 240
        y = 12
        for col, text in legend:
            pygame.draw.rect(self.screen, col, (x, y, 18, 12))
            self.screen.blit(self.small_font.render(text, True, BLACK), (x + 26, y - 2))
            y += 20

    # -------------------- Main loop --------------------
    def draw(self):
        self.screen.fill(WHITE)
        self._draw_road()
        self._draw_vehicles()
        self._draw_traffic_lights()
        self._draw_hud()
        pygame.display.flip()

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
                        self.speedup = min(12, self.speedup + 1)
                    elif event.key == pygame.K_DOWN:
                        self.speedup = max(1, self.speedup - 1)
                    elif event.key == pygame.K_RIGHT:
                        # aumentar spawn de ambas vías (limitado)
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
            self.clock.tick(30)

        pygame.quit()
        sys.exit()
