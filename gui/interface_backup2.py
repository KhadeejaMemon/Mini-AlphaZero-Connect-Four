import copy
import json
import math
import os
import queue
import random
import sys
import threading
import time


def find_root():
    """Find the project root (the folder that contains 'game')."""
    folder = os.path.dirname(os.path.abspath(__file__))
    for _ in range(3):
        if os.path.isdir(os.path.join(folder, "game")):
            return folder
        folder = os.path.dirname(folder)
    return os.getcwd()


ROOT = find_root()
sys.path.insert(0, ROOT)

# Keep the window sharp (not blurry / tiny) with Windows display scaling
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import pygame
import pygame.gfxdraw

from game.connect_four import ConnectFour
from agents.random_ai import RandomAI
from agents.minimax import MinimaxAI
from agents.alpha_beta import AlphaBetaAI
from agents.mcts import MCTSAI

# try:
#     from agents.neural_mcts import NeuralMCTSAI
# except Exception:
#     NeuralMCTSAI = None

try:
    from agents.neural_mcts import NeuralMCTSAI
except Exception as error:
    print("Neural MCTS import failed:", error)
    NeuralMCTSAI = None


pygame.init()

MODEL_PATH = os.path.join(ROOT, "results", "models", "connect4_model.pth")
print("ROOT:", ROOT)
print("MODEL:", MODEL_PATH, "exists:", os.path.exists(MODEL_PATH))
# ------------------------------------------------------------------ scaling
# Designed on a 1200 x 920 canvas, scaled to fit the screen.
BASE_W, BASE_H = 1200, 920

_info = pygame.display.Info()
_screen_w = _info.current_w if _info.current_w > 0 else 1920
_screen_h = _info.current_h if _info.current_h > 0 else 1080

SCALE = max(
    0.6,
    min(_screen_w * 0.94 / BASE_W, _screen_h * 0.86 / BASE_H, 2.0)
)


def u(value):
    """Convert a design unit to real pixels."""
    return int(round(value * SCALE))


# ------------------------------------------------------------------ layout
WIDTH, HEIGHT = u(BASE_W), u(BASE_H)

ROWS, COLS = 6, 7
CELL = u(100)
BOARD_X, BOARD_Y = u(40), u(215)
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL

HOLE_R = int(CELL * 0.40)
PIECE_R = int(CELL * 0.42)
INNER_R = int(CELL * 0.28)
PREVIEW_Y = BOARD_Y - u(60)

PANEL = pygame.Rect(u(770), u(104), u(390), u(714))
PX = PANEL.x + u(20)          # left margin inside the panel
PW = PANEL.width - u(40)      # usable width inside the panel
GAP = u(10)

# y positions inside the panel (design units)
Y_OPP, Y_BTN0, BTN_STEP, BTN_H = u(126), u(156), u(52), u(44)
Y_STR, Y_LVL, SMALL_H = u(428), u(458), u(42)
Y_YOU, Y_SIDE = u(520), u(550)
Y_SCORE, Y_BOX, BOX_H = u(612), u(642), u(84)
Y_ACT, ACT_H = u(746), u(50)

# ------------------------------------------------------------------ themes
THEMES = {
    "Light": {
        "BG": (238, 242, 247),
        "PANEL_BG": (255, 255, 255),
        "PANEL_EDGE": (211, 219, 231),
        "SHADOW": (205, 212, 225),
        "HOLE_BG": (222, 229, 240),
        "BOARD_BLUE": (37, 99, 235),
        "BOARD_DARK": (29, 78, 190),
        "BTN": (241, 245, 249),
        "BTN_HOVER": (226, 232, 240),
        "BORDER": (200, 210, 224),
        "TEXT": (30, 41, 59),
        "MUTED": (100, 116, 139),
        "ACCENT": (37, 99, 235),
        "DISABLED": (203, 213, 225),
        "VEIL": (238, 242, 247, 205),
    },
    "Dark": {
        "BG": (15, 20, 33),
        "PANEL_BG": (28, 36, 54),
        "PANEL_EDGE": (55, 65, 90),
        "SHADOW": (7, 10, 18),
        "HOLE_BG": (10, 14, 24),
        "BOARD_BLUE": (37, 99, 235),
        "BOARD_DARK": (29, 78, 190),
        "BTN": (42, 53, 76),
        "BTN_HOVER": (58, 72, 102),
        "BORDER": (72, 86, 120),
        "TEXT": (240, 244, 250),
        "MUTED": (160, 174, 198),
        "ACCENT": (59, 130, 246),
        "DISABLED": (72, 86, 120),
        "VEIL": (15, 20, 33, 215),
    },
        "Pink": {
        "BG": (253, 242, 248),
        "PANEL_BG": (255, 255, 255),
        "PANEL_EDGE": (251, 207, 232),
        "SHADOW": (244, 200, 222),
        "HOLE_BG": (252, 231, 243),
        "BOARD_BLUE": (190, 24, 93),
        "BOARD_DARK": (157, 23, 77),
        "BTN": (253, 242, 248),
        "BTN_HOVER": (252, 231, 243),
        "BORDER": (249, 168, 212),
        "TEXT": (80, 7, 36),
        "MUTED": (131, 24, 67),
        "ACCENT": (219, 39, 119),
        "DISABLED": (249, 168, 212),
        "VEIL": (253, 242, 248, 210),
    },
    "Maroon": {
        "BG": (28, 10, 14),
        "PANEL_BG": (46, 16, 24),
        "PANEL_EDGE": (110, 38, 52),
        "SHADOW": (12, 4, 6),
        "HOLE_BG": (20, 6, 10),
        "BOARD_BLUE": (128, 0, 32),
        "BOARD_DARK": (96, 0, 24),
        "BTN": (70, 24, 34),
        "BTN_HOVER": (96, 34, 48),
        "BORDER": (140, 52, 68),
        "TEXT": (255, 240, 242),
        "MUTED": (230, 190, 198),
        "ACCENT": (190, 18, 60),
        "DISABLED": (110, 38, 52),
        "VEIL": (28, 10, 14, 215),
    },
        "Black": {
        "BG": (0, 0, 0),
        "PANEL_BG": (15, 15, 18),
        "PANEL_EDGE": (45, 45, 52),
        "SHADOW": (0, 0, 0),
        "HOLE_BG": (8, 8, 10),
        "BOARD_BLUE": (30, 58, 138),
        "BOARD_DARK": (23, 37, 84),
        "BTN": (30, 30, 36),
        "BTN_HOVER": (45, 45, 54),
        "BORDER": (63, 63, 74),
        "TEXT": (250, 250, 250),
        "MUTED": (176, 176, 190),
        "ACCENT": (59, 130, 246),
        "DISABLED": (63, 63, 74),
        "VEIL": (0, 0, 0, 215),
    },
    "Ocean": {
        "BG": (236, 248, 251),
        "PANEL_BG": (255, 255, 255),
        "PANEL_EDGE": (186, 230, 253),
        "SHADOW": (190, 222, 236),
        "HOLE_BG": (214, 238, 246),
        "BOARD_BLUE": (14, 116, 144),
        "BOARD_DARK": (21, 94, 117),
        "BTN": (240, 249, 255),
        "BTN_HOVER": (224, 242, 254),
        "BORDER": (165, 214, 235),
        "TEXT": (8, 47, 73),
        "MUTED": (51, 85, 105),
        "ACCENT": (2, 132, 199),
        "DISABLED": (186, 230, 253),
        "VEIL": (236, 248, 251, 210),
    },
    "Forest": {
        "BG": (10, 25, 18),
        "PANEL_BG": (18, 42, 30),
        "PANEL_EDGE": (40, 84, 62),
        "SHADOW": (4, 12, 8),
        "HOLE_BG": (6, 18, 12),
        "BOARD_BLUE": (22, 101, 52),
        "BOARD_DARK": (20, 83, 45),
        "BTN": (28, 62, 44),
        "BTN_HOVER": (40, 84, 62),
        "BORDER": (56, 112, 82),
        "TEXT": (236, 253, 245),
        "MUTED": (167, 215, 190),
        "ACCENT": (22, 163, 74),
        "DISABLED": (40, 84, 62),
        "VEIL": (10, 25, 18, 215),
    },
    "Purple": {
        "BG": (245, 243, 255),
        "PANEL_BG": (255, 255, 255),
        "PANEL_EDGE": (221, 214, 254),
        "SHADOW": (214, 208, 240),
        "HOLE_BG": (233, 228, 252),
        "BOARD_BLUE": (109, 40, 217),
        "BOARD_DARK": (91, 33, 182),
        "BTN": (245, 243, 255),
        "BTN_HOVER": (237, 233, 254),
        "BORDER": (196, 181, 253),
        "TEXT": (46, 16, 101),
        "MUTED": (87, 63, 140),
        "ACCENT": (124, 58, 237),
        "DISABLED": (196, 181, 253),
        "VEIL": (245, 243, 255, 210),
    },
    "Sunset": {
        "BG": (255, 247, 237),
        "PANEL_BG": (255, 255, 255),
        "PANEL_EDGE": (254, 215, 170),
        "SHADOW": (245, 215, 185),
        "HOLE_BG": (254, 235, 215),
        "BOARD_BLUE": (180, 60, 15),
        "BOARD_DARK": (140, 45, 12),
        "BTN": (255, 247, 237),
        "BTN_HOVER": (254, 235, 215),
        "BORDER": (253, 186, 116),
        "TEXT": (67, 20, 7),
        "MUTED": (124, 45, 18),
        "ACCENT": (234, 88, 12),
        "DISABLED": (253, 186, 116),
        "VEIL": (255, 247, 237, 210),
    },
}

THEME_ORDER = [
    "Light", "Dark", "Black", "Ocean", "Forest",
    "Purple", "Sunset", "Pink", "Maroon"
]

# Same in every theme
WHITE = (255, 255, 255)
MARKER = (30, 41, 59)
GREEN = (22, 163, 74)
GREEN_HOVER = (34, 180, 90)
RED_UI = (220, 53, 69)
AMBER = (217, 119, 6)
GREY_PILL = (100, 116, 139)

SETTINGS_PATH = os.path.join(ROOT, "results", "gui_settings.json")


def load_theme():
    try:
        with open(SETTINGS_PATH) as file:
            name = json.load(file).get("theme")
        if name in THEMES:
            return name
    except Exception:
        pass
    return "Light"


def save_theme(name):
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w") as file:
            json.dump({"theme": name}, file)
    except Exception:
        pass


THEME_NAME = load_theme()
globals().update(THEMES[THEME_NAME])

PLAYER_COLOR = {1: (250, 204, 21), -1: (239, 68, 68)}

AI_NAMES = [
    "Random AI", "Minimax", "Alpha-Beta", "Standard MCTS", "Neural MCTS"
]

# level -> (minimax depth, MCTS simulations)
LEVELS = {
    "Easy": (2, 50),
    "Medium": (3, 100),
    "Hard": (4, 200),
}


# ------------------------------------------------------------------ helpers
def neural_status():
    if NeuralMCTSAI is None:
        return False, "Neural MCTS could not be loaded (PyTorch missing?)."
    if not os.path.exists(MODEL_PATH):
        return False, "No trained model found. Run iterate.py first."
    return True, ""


def make_ai(name, level):
    depth, sims = LEVELS[level]

    if name == "Random AI":
        return RandomAI()
    if name == "Minimax":
        return MinimaxAI(depth=depth)
    if name == "Alpha-Beta":
        return AlphaBetaAI(depth=depth + 1)
    if name == "Standard MCTS":
        return MCTSAI(simulations=sims)
    if name == "Neural MCTS":
        return NeuralMCTSAI(model_path=MODEL_PATH, simulations=sims)

    raise ValueError(name)


def level_description(name, level):
    depth, sims = LEVELS[level]

    if name == "Random AI":
        return "no effect"
    if name == "Minimax":
        return f"depth {depth}"
    if name == "Alpha-Beta":
        return f"depth {depth + 1}"
    return f"{sims} simulations"


def find_win(board, player):
    """Return the four winning cells."""
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                cells = [(r + dr * i, c + dc * i) for i in range(4)]
                if all(
                    0 <= a < ROWS and 0 <= b < COLS and board[a][b] == player
                    for a, b in cells
                ):
                    return cells
    return []


def shade(color, factor):
    return tuple(max(0, min(255, int(v * factor))) for v in color)


def disc(surface, color, center, radius):
    x, y = int(center[0]), int(center[1])
    pygame.gfxdraw.aacircle(surface, x, y, radius, color)
    pygame.gfxdraw.filled_circle(surface, x, y, radius, color)


def make_font(size, bold=False):
    return pygame.font.SysFont(
        "segoeui,helvetica,arial,dejavusans", u(size), bold=bold
    )


def short(message, limit=62):
    return message if len(message) <= limit else message[:limit - 3] + "..."


# ------------------------------------------------------------------ app
class App:

    def __init__(self):

        pygame.display.set_caption("Mini-AlphaZero | Connect Four")

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.f_title = make_font(42, True)
        self.f_start = make_font(34, True)
        self.f_big = make_font(36, True)
        self.f_med = make_font(26, True)
        self.f_norm = make_font(22)
        self.f_small = make_font(18, True)
        self.f_hero = make_font(68, True)

        self.theme = THEME_NAME
        self.mask = self.build_mask()

        self.theme_rect = pygame.Rect(
            BOARD_X + BOARD_W - u(170), u(30), u(170), u(52)
        )

        self.start_rect = pygame.Rect(0, 0, u(340), u(90))
        self.start_rect.center = (
            BOARD_X + BOARD_W // 2, BOARD_Y + BOARD_H // 2 - u(20)
        )

        self.result_queue = queue.Queue()
        self.token = 0
        self.thinking = False

        self.human = 1
        self.level = "Medium"
        self.score = {"you": 0, "ai": 0, "draw": 0}
        self.msg = ""
        self.ai = None

        self.neural_ok, self.neural_reason = neural_status()

        self.opponent = "Neural MCTS" if self.neural_ok else "Standard MCTS"

        if not self.set_ai(self.opponent):
            self.opponent = "Standard MCTS"
            self.set_ai(self.opponent)

        self.mode = "ai"            # "ai" or "two"
        self.state = "home"         # "home" or "game"
        self.fade = 255
        self.t0 = time.time()
        self.layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.fade_surf = pygame.Surface((WIDTH, HEIGHT))
        self.particles = self.make_particles()
        self.confetti = []
        self.home_buttons = self.build_home_buttons()

        self.buttons = self.build_buttons()
        self.new_game(started=False)

    # -------------------------------------------------------- setup
    def build_mask(self):
        """Blue board with holes. Pieces fall behind it."""

        mask = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)

        pygame.draw.rect(
            mask, BOARD_BLUE, (0, 0, BOARD_W, BOARD_H),
            border_radius=u(20)
        )

        rim = max(2, u(4))

        for r in range(ROWS):
            for c in range(COLS):
                center = (c * CELL + CELL // 2, r * CELL + CELL // 2)
                pygame.draw.circle(
                    mask, BOARD_DARK, center, HOLE_R + rim, rim
                )
                pygame.draw.circle(mask, (0, 0, 0, 0), center, HOLE_R)

        return mask

    def build_buttons(self):

        buttons = []

        for i, name in enumerate(AI_NAMES):
            buttons.append((
                ("ai", name),
                pygame.Rect(PX, Y_BTN0 + i * BTN_STEP, PW, BTN_H),
                name
            ))

        third = (PW - 2 * GAP) // 3
        half = (PW - GAP) // 2

        for i, level in enumerate(LEVELS):
            buttons.append((
                ("level", level),
                pygame.Rect(PX + i * (third + GAP), Y_LVL, third, SMALL_H),
                level
            ))

        buttons.append((
            ("side", 1),
            pygame.Rect(PX, Y_SIDE, half, SMALL_H),
            "First (Yellow)"
        ))
        buttons.append((
            ("side", -1),
            pygame.Rect(PX + half + GAP, Y_SIDE, half, SMALL_H),
            "Second (Red)"
        ))

        for i, (name, label) in enumerate(
            [("undo", "Undo"), ("restart", "Restart"), ("exit", "Menu")]
        ):
            buttons.append((
                name,
                pygame.Rect(PX + i * (third + GAP), Y_ACT, third, ACT_H),
                label
            ))

        return buttons

    def set_ai(self, name):

        try:
            self.ai = make_ai(name, self.level)
            return True

        except Exception as error:
            self.msg = short(f"Could not load {name}: {error}")
            return False

    # -------------------------------------------------------- theme
    def apply_theme(self, name):

        globals().update(THEMES[name])
        self.theme = name
        self.mask = self.build_mask()
        save_theme(name)

    def toggle_theme(self):

        index = THEME_ORDER.index(self.theme)
        self.apply_theme(THEME_ORDER[(index + 1) % len(THEME_ORDER)])

    # -------------------------------------------------------- home page
    def make_particles(self):
        items = []
        for _ in range(26):
            items.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(-HEIGHT, HEIGHT),
                "v": random.uniform(1.5, 4.5) * SCALE,
                "r": random.randint(u(16), u(40)),
                "p": random.choice((1, -1)),
            })
        return items

    def build_home_buttons(self):
        w, h = u(420), u(80)
        x = WIDTH // 2 - w // 2
        top = u(420)
        return [
            ("ai", pygame.Rect(x, top, w, h), "Play vs AI"),
            ("two", pygame.Rect(x, top + u(100), w, h), "2 Players"),
            ("quit", pygame.Rect(x, top + u(200), w, h), "Quit"),
        ]

    def start_mode(self, mode):
        self.mode = mode
        self.state = "game"
        self.fade = 255
        self.msg = ""
        self.score = {"you": 0, "ai": 0, "draw": 0}
        self.new_game(started=True)

    def go_home(self):
        self.token += 1
        self.thinking = False
        self.state = "home"
        self.fade = 255
        self.msg = ""

    def draw_home(self):
        screen = self.screen
        now = time.time() - self.t0

        # Falling translucent discs in the background
        self.layer.fill((0, 0, 0, 0))
        for p in self.particles:
            p["y"] += p["v"]
            if p["y"] > HEIGHT + p["r"]:
                p["y"] = -p["r"]
                p["x"] = random.uniform(0, WIDTH)
            sway = math.sin(now * 1.5 + p["x"]) * u(12)
            color = PLAYER_COLOR[p["p"]] + (70,)
            disc(self.layer, color, (p["x"] + sway, p["y"]), p["r"])
        screen.blit(self.layer, (0, 0))

        # Waving title
        title = "MINI-ALPHAZERO"
        widths = [self.f_hero.size(ch)[0] for ch in title]
        x = WIDTH // 2 - sum(widths) // 2
        for i, ch in enumerate(title):
            y = u(130) + int(math.sin(now * 3 + i * 0.5) * u(10))
            self.text(ch, (x, y), self.f_hero, ACCENT if i % 2 == 0 else TEXT)
            x += widths[i]

        self.text(
            "Connect Four  |  CNN + Monte Carlo Tree Search",
            (WIDTH // 2, u(240)), self.f_norm, MUTED, "center"
        )

        # Bouncing discs
        for i in range(7):
            cx = WIDTH // 2 + (i - 3) * u(80)
            cy = u(340) - int(abs(math.sin(now * 2.5 + i * 0.7)) * u(30))
            disc(screen, PLAYER_COLOR[1 if i % 2 == 0 else -1], (cx, cy), u(28))

        # Buttons (pulse, grow on hover)
        mouse = pygame.mouse.get_pos()
        for i, (bid, rect, label) in enumerate(self.home_buttons):
            hover = rect.collidepoint(mouse)
            grow = u(8) if hover else int(math.sin(now * 3 + i) * u(3))
            r = rect.inflate(grow * 2, grow)

            if bid == "ai":
                bg, fg = (GREEN_HOVER if hover else GREEN), WHITE
            elif bid == "two":
                bg, fg = ACCENT, WHITE
            else:
                bg, fg = (BTN_HOVER if hover else BTN), TEXT

            pygame.draw.rect(screen, bg, r, border_radius=u(22))
            if bid == "quit":
                pygame.draw.rect(screen, BORDER, r, 2, border_radius=u(22))
            self.text(label, r.center, self.f_start, fg, "center")

        self.text(
            "1 vs AI   |   2 Two players   |   T theme   |   ESC quit",
            (WIDTH // 2, HEIGHT - u(40)), self.f_small, MUTED, "center"
        )
        self.draw_button(self.theme_rect, f"Theme: {self.theme}")

    # -------------------------------------------------------- confetti
    def spawn_confetti(self):
        colors = [(250, 204, 21), (239, 68, 68), (59, 130, 246),
                  (34, 197, 94), (255, 255, 255)]
        for _ in range(120):
            self.confetti.append({
                "x": random.uniform(0, WIDTH),
                "y": random.uniform(-u(200), 0),
                "vx": random.uniform(-1.5, 1.5) * SCALE,
                "vy": random.uniform(2, 6) * SCALE,
                "c": random.choice(colors),
                "s": random.randint(u(5), u(10)),
            })

    def draw_confetti(self):
        alive = []
        for c in self.confetti:
            c["x"] += c["vx"]
            c["y"] += c["vy"]
            if c["y"] < HEIGHT:
                pygame.draw.rect(
                    self.screen, c["c"], (int(c["x"]), int(c["y"]), c["s"], c["s"])
                )
                alive.append(c)
        self.confetti = alive

    # -------------------------------------------------------- 2-player panel
    def draw_panel_two(self):
        screen = self.screen

        pygame.draw.rect(screen, PANEL_BG, PANEL, border_radius=u(18))
        pygame.draw.rect(screen, PANEL_EDGE, PANEL, 2, border_radius=u(18))

        self.text("TWO PLAYER MODE", (PX, Y_OPP), self.f_small, MUTED)

        current = self.game.current_player
        for i, (player, name) in enumerate(
            ((1, "Player 1  (Yellow)"), (-1, "Player 2  (Red)"))
        ):
            rect = pygame.Rect(PX, Y_BTN0 + i * u(80), PW, u(64))
            active = (
                self.started and not self.game.game_over and current == player
            )
            pygame.draw.rect(
                screen, ACCENT if active else BTN, rect, border_radius=u(14)
            )
            if not active:
                pygame.draw.rect(screen, BORDER, rect, 2, border_radius=u(14))
            disc(screen, PLAYER_COLOR[player], (rect.x + u(36), rect.centery), u(20))
            self.text(
                name, (rect.x + u(74), rect.centery), self.f_norm,
                WHITE if active else TEXT, "midleft"
            )

        self.text("Take turns on the same screen.", (PX, Y_STR), self.f_small, MUTED)
        self.text("Click a column or press 1-7.", (PX, Y_STR + u(30)), self.f_small, MUTED)

        self.text("SCORE", (PX, Y_SCORE), self.f_small, MUTED)
        third = (PW - 2 * GAP) // 3
        boxes = [
            ("Yellow", self.score["you"]),
            ("Red", self.score["ai"]),
            ("Draws", self.score["draw"]),
        ]
        for i, (label, value) in enumerate(boxes):
            rect = pygame.Rect(PX + i * (third + GAP), Y_BOX, third, BOX_H)
            pygame.draw.rect(screen, BTN, rect, border_radius=u(12))
            pygame.draw.rect(screen, BORDER, rect, 2, border_radius=u(12))
            self.text(str(value), (rect.centerx, rect.y + u(8)),
                      self.f_big, TEXT, "midtop")
            self.text(label, (rect.centerx, rect.y + u(56)),
                      self.f_small, MUTED, "midtop")

        for button_id, rect, label in self.buttons:
            if not isinstance(button_id, tuple):
                self.draw_button(rect, label)

    # -------------------------------------------------------- game state
    def new_game(self, started=False):

        self.token += 1          # ignore results from any old AI thread
        self.thinking = False

        self.started = started
        self.game = ConnectFour()
        self.moves = []          # list of (column, player)
        self.anim = None
        self.win_cells = []
        self.last_move = None
        self.last_info = ""
        self.counted = False
        self.result_key = None
        self.confetti = []

    def start(self):
        if not self.started:
            self.msg = ""
            self.started = True

    def human_turn(self):
        return (
            self.started
            and not self.game.game_over
            and self.anim is None
            and not self.thinking
            and (self.mode == "two" or self.game.current_player == self.human)
        )

    def place(self, col):

        game = self.game
        player = game.current_player

        row = next(
            r for r in range(ROWS - 1, -1, -1) if game.board[r][col] == 0
        )

        if not game.make_move(col):
            return False

        self.moves.append((col, player))
        self.last_move = (row, col)

        self.anim = {
            "row": row,
            "col": col,
            "player": player,
            "y": float(BOARD_Y - CELL // 2),
            "vy": 0.0,
            "bounced": False,
        }

        return True

    def human_move(self, col):

        if self.human_turn() and col in self.game.get_valid_moves():
            self.place(col)

    def undo(self):

        if not self.started or not self.moves or self.anim is not None:
            return

        # If the AI opened the game, there is nothing sensible to undo
        if (self.mode == "ai" and len(self.moves) == 1
                and self.moves[0][1] != self.human):
            return

        self.token += 1
        self.thinking = False

        if self.counted:
            self.score[self.result_key] -= 1
            self.counted = False
            self.result_key = None
            self.win_cells = []

        removed = self.moves.pop()

        if self.mode == "ai" and removed[1] != self.human and self.moves:
            self.moves.pop()

        remaining = self.moves[:]

        self.game = ConnectFour()
        self.moves = []

        for col, player in remaining:
            self.game.make_move(col)
            self.moves.append((col, player))

        self.last_move = None

        if remaining:
            col = remaining[-1][0]
            for r in range(ROWS):
                if self.game.board[r][col] != 0:
                    self.last_move = (r, col)
                    break

    # -------------------------------------------------------- AI thread
    def start_ai(self):

        self.token += 1
        token = self.token
        self.thinking = True

        snapshot = copy.deepcopy(self.game)
        ai = self.ai

        def work():

            start = time.perf_counter()

            try:
                move = ai.get_move(snapshot)
                error = None

            except Exception as exc:
                move, error = None, str(exc)

            elapsed = time.perf_counter() - start

            # If the move was instant, wait a little so it feels natural
            if elapsed < 0.45:
                time.sleep(0.45 - elapsed)

            self.result_queue.put((token, move, elapsed, error))

        threading.Thread(target=work, daemon=True).start()

    def poll_ai(self):

        try:
            token, move, elapsed, error = self.result_queue.get_nowait()
        except queue.Empty:
            return

        if token != self.token or not self.thinking:
            return

        self.thinking = False

        valid = self.game.get_valid_moves()

        if not valid:
            return

        if error:
            self.msg = short(f"AI error: {error}")

        if move not in valid:
            move = random.choice(valid)
            self.msg = self.msg or "AI returned an invalid move; played randomly."

        self.last_info = (
            f"AI played column {move + 1} in {elapsed:.2f}s"
        )

        self.place(move)

    # -------------------------------------------------------- update
    def update(self):

        # Falling piece animation
        anim = self.anim

        if anim is not None:

            target = BOARD_Y + anim["row"] * CELL + CELL / 2

            anim["vy"] += 1.7 * SCALE
            anim["y"] += anim["vy"]

            if anim["y"] >= target:
                anim["y"] = target

                if not anim["bounced"] and anim["vy"] > 9 * SCALE:
                    anim["vy"] = -anim["vy"] * 0.25
                    anim["bounced"] = True
                else:
                    self.anim = None

        # Game finished (after the last piece has landed): update the score
        if (
            self.anim is None
            and self.game.game_over
            and not self.counted
        ):
            self.counted = True
            winner = self.game.winner

            if winner in (1, -1):
                self.win_cells = find_win(self.game.board, winner)
                if self.mode == "two":
                    self.result_key = "you" if winner == 1 else "ai"
                else:
                    self.result_key = "you" if winner == self.human else "ai"

                if self.mode == "two" or winner == self.human:
                    self.spawn_confetti()
            else:
                self.result_key = "draw"

            self.score[self.result_key] += 1

        self.poll_ai()

        if (
            self.started
            and not self.game.game_over
            and self.anim is None
            and not self.thinking
            and self.state == "game"
            and self.mode == "ai"
            and self.game.current_player != self.human
        ):
            self.start_ai()

    # -------------------------------------------------------- input
    def is_selected(self, button_id):

        if isinstance(button_id, tuple):
            kind, value = button_id

            if kind == "ai":
                return value == self.opponent
            if kind == "level":
                return value == self.level
            if kind == "side":
                return value == self.human

        return False

    def click(self, pos):
        """Return True if Exit was pressed."""

        self.msg = ""

        if self.theme_rect.collidepoint(pos):
            self.toggle_theme()
            return False

        if self.state == "home":
            for bid, rect, _ in self.home_buttons:
                if rect.collidepoint(pos):
                    if bid == "quit":
                        return True
                    self.start_mode(bid)
                    break
            return False

        if not self.started and self.start_rect.collidepoint(pos):
            self.start()
            return False

        for button_id, rect, _ in self.buttons:

            if not rect.collidepoint(pos):
                continue

            if self.mode == "two" and isinstance(button_id, tuple):
                continue

            if button_id == "exit":
                self.go_home()
                return False

            if button_id == "restart":
                self.new_game(started=True)

            elif button_id == "undo":
                self.undo()

            else:
                kind, value = button_id

                if kind == "ai":

                    if value == "Neural MCTS" and not self.neural_ok:
                        self.msg = self.neural_reason
                        return False

                    previous = self.opponent
                    self.opponent = value

                    if self.set_ai(value):
                        self.score = {"you": 0, "ai": 0, "draw": 0}
                        self.new_game(started=False)
                    else:
                        self.opponent = previous

                elif kind == "level":
                    self.level = value

                    if self.set_ai(self.opponent):
                        self.new_game(started=False)

                elif kind == "side":
                    self.human = value
                    self.new_game(started=False)

            return False

        # Click on the board
        x, y = pos

        if (
            BOARD_X <= x < BOARD_X + BOARD_W
            and BOARD_Y - u(110) <= y < BOARD_Y + BOARD_H
        ):
            self.human_move((x - BOARD_X) // CELL)

        return False

    # -------------------------------------------------------- drawing
    def text(self, content, pos, font, color=None, anchor="topleft"):

        if color is None:
            color = TEXT

        image = font.render(content, True, color)
        rect = image.get_rect()
        setattr(rect, anchor, pos)
        self.screen.blit(image, rect)

        return rect

    def draw_piece(self, cx, cy, player):

        color = PLAYER_COLOR[player]

        disc(self.screen, shade(color, 0.8), (cx, cy), PIECE_R)
        disc(self.screen, color, (cx, cy), PIECE_R - u(2))

        pygame.draw.circle(
            self.screen, shade(color, 0.86), (cx, cy), INNER_R, max(2, u(4))
        )

    def draw_button(self, rect, label, selected=False, dim=False):

        hover = rect.collidepoint(pygame.mouse.get_pos())

        if selected:
            background, foreground = ACCENT, WHITE
        else:
            background = BTN_HOVER if hover else BTN
            foreground = MUTED if dim else TEXT

        pygame.draw.rect(
            self.screen, background, rect, border_radius=u(11)
        )

        if not selected:
            pygame.draw.rect(
                self.screen, BORDER, rect, 2, border_radius=u(11)
            )

        self.text(label, rect.center, self.f_norm, foreground, "center")

    def status(self):

        if not self.started:
            return "Press START", GREY_PILL

        if self.game.game_over and self.anim is None:

            winner = self.game.winner

            if winner == 0:
                return "Draw!", GREY_PILL
            if self.mode == "two":
                return ("Yellow wins!" if winner == 1 else "Red wins!"), GREEN
            if winner == self.human:
                return "You won!", GREEN
            return "AI won!", RED_UI

        if self.thinking:
            dots = "." * (1 + int(time.time() * 3) % 3)
            return "AI is thinking" + dots, AMBER

        if self.mode == "two":
            who = "Yellow's turn" if self.game.current_player == 1 else "Red's turn"
            return who, GREEN

        if self.game.current_player == self.human:
            return "Your turn", GREEN

        return "AI's turn", AMBER

    def draw_header(self):

        self.text("MINI-ALPHAZERO", (BOARD_X, u(16)), self.f_title)
        self.text(
            "Connect Four  |  CNN + Monte Carlo Tree Search",
            (BOARD_X, u(72)), self.f_norm, MUTED
        )

        # Status pill sits above the side panel so it never overlaps the title
        label, color = self.status()
        pill = pygame.Rect(PANEL.x, u(26), PANEL.width, u(60))

        pygame.draw.rect(self.screen, color, pill, border_radius=u(30))
        self.text(label, pill.center, self.f_med, WHITE, "center")

        self.draw_button(self.theme_rect, f"Theme: {self.theme}")

    def draw_board(self):

        screen = self.screen
        board = self.game.board

        # Soft shadow + hole background
        pygame.draw.rect(
            screen, SHADOW,
            (BOARD_X + u(4), BOARD_Y + u(8), BOARD_W, BOARD_H),
            border_radius=u(20)
        )
        pygame.draw.rect(
            screen, HOLE_BG,
            (BOARD_X, BOARD_Y, BOARD_W, BOARD_H), border_radius=u(20)
        )

        # Hover column (only on the human's turn)
        mx, my = pygame.mouse.get_pos()
        hover_col = None

        if (
            self.human_turn()
            and BOARD_X <= mx < BOARD_X + BOARD_W
            and BOARD_Y - u(110) <= my < BOARD_Y + BOARD_H
        ):
            hover_col = (mx - BOARD_X) // CELL

        # Preview piece above the board
        if hover_col is not None:
            cx = BOARD_X + hover_col * CELL + CELL // 2

            if hover_col in self.game.get_valid_moves():
                self.draw_piece(cx, PREVIEW_Y, self.game.current_player)
            else:
                disc(screen, DISABLED, (cx, PREVIEW_Y), PIECE_R)

        # Pieces
        for r in range(ROWS):
            for c in range(COLS):

                value = board[r][c]

                if value == 0:
                    continue

                if (
                    self.anim is not None
                    and (r, c) == (self.anim["row"], self.anim["col"])
                ):
                    continue

                self.draw_piece(
                    BOARD_X + c * CELL + CELL // 2,
                    BOARD_Y + r * CELL + CELL // 2,
                    int(value)
                )

        if self.anim is not None:
            self.draw_piece(
                BOARD_X + self.anim["col"] * CELL + CELL // 2,
                int(self.anim["y"]),
                self.anim["player"]
            )

        # Board face (with holes)
        screen.blit(self.mask, (BOARD_X, BOARD_Y))

        # Highlight the hovered column
        if hover_col is not None and hover_col in self.game.get_valid_moves():
            strip = pygame.Surface((CELL, BOARD_H), pygame.SRCALPHA)
            strip.fill((255, 255, 255, 38))
            screen.blit(strip, (BOARD_X + hover_col * CELL, BOARD_Y))

        # Last move marker
        if self.last_move is not None and self.anim is None:
            r, c = self.last_move
            pygame.draw.circle(
                screen, MARKER,
                (BOARD_X + c * CELL + CELL // 2,
                 BOARD_Y + r * CELL + CELL // 2),
                u(8)
            )

        # Winning four
        if self.win_cells:
            pulse = int(u(3) * math.sin(time.time() * 6))

            for r, c in self.win_cells:
                pygame.draw.circle(
                    screen, WHITE,
                    (BOARD_X + c * CELL + CELL // 2,
                     BOARD_Y + r * CELL + CELL // 2),
                    HOLE_R + u(3) + pulse, max(3, u(5))
                )

        # Start overlay
        if not self.started:
            veil = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
            pygame.draw.rect(
                veil, VEIL, (0, 0, BOARD_W, BOARD_H),
                border_radius=u(20)
            )
            screen.blit(veil, (BOARD_X, BOARD_Y))

            hover = self.start_rect.collidepoint(pygame.mouse.get_pos())

            pygame.draw.rect(
                screen, GREEN_HOVER if hover else GREEN,
                self.start_rect, border_radius=u(22)
            )
            self.text(
                "START GAME", self.start_rect.center,
                self.f_start, WHITE, "center"
            )
            self.text(
                "Choose your opponent on the right, then press Start",
                (self.start_rect.centerx, self.start_rect.bottom + u(36)),
                self.f_norm, TEXT, "center"
            )

        # Info line + hints under the board
        y = BOARD_Y + BOARD_H + u(18)

        if self.msg:
            self.text(self.msg, (BOARD_X, y), self.f_norm, AMBER)
        elif self.last_info:
            self.text(self.last_info, (BOARD_X, y), self.f_norm, MUTED)

        self.text(
            "Click a column or 1-7  |  U undo  |  R restart  |  "
            "T theme  |  ESC menu",
            (BOARD_X, y + u(36)), self.f_small, MUTED
        )

    def draw_panel(self):

        if self.mode == "two":
            self.draw_panel_two()
            return

        screen = self.screen

        pygame.draw.rect(screen, PANEL_BG, PANEL, border_radius=u(18))
        pygame.draw.rect(screen, PANEL_EDGE, PANEL, 2, border_radius=u(18))

        self.text("OPPONENT", (PX, Y_OPP), self.f_small, MUTED)

        self.text("STRENGTH", (PX, Y_STR), self.f_small, MUTED)
        self.text(
            level_description(self.opponent, self.level),
            (PX + PW, Y_STR), self.f_small, MUTED, "topright"
        )

        self.text("YOU PLAY", (PX, Y_YOU), self.f_small, MUTED)
        self.text("SCORE", (PX, Y_SCORE), self.f_small, MUTED)

        for button_id, rect, label in self.buttons:

            dim = False

            if isinstance(button_id, tuple):
                kind, value = button_id

                if kind == "ai" and value == "Neural MCTS" \
                        and not self.neural_ok:
                    label = "Neural MCTS (no model)"
                    dim = True

                if kind == "level" and self.opponent == "Random AI":
                    dim = True

            self.draw_button(
                rect, label, self.is_selected(button_id), dim
            )

        # Scoreboard
        third = (PW - 2 * GAP) // 3

        boxes = [
            ("You", self.score["you"]),
            ("AI", self.score["ai"]),
            ("Draws", self.score["draw"]),
        ]

        for i, (label, value) in enumerate(boxes):

            rect = pygame.Rect(
                PX + i * (third + GAP), Y_BOX, third, BOX_H
            )

            pygame.draw.rect(screen, BTN, rect, border_radius=u(12))
            pygame.draw.rect(screen, BORDER, rect, 2, border_radius=u(12))

            self.text(
                str(value), (rect.centerx, rect.y + u(8)),
                self.f_big, TEXT, "midtop"
            )
            self.text(
                label, (rect.centerx, rect.y + u(56)),
                self.f_small, MUTED, "midtop"
            )

    def draw(self):

        self.screen.fill(BG)

        if self.state == "home":
            self.draw_home()
        else:
            self.draw_header()
            self.draw_board()
            self.draw_panel()
            self.draw_confetti()

        # Fade-in transition between pages
        if self.fade > 0:
            self.fade_surf.fill(BG)
            self.fade_surf.set_alpha(self.fade)
            self.screen.blit(self.fade_surf, (0, 0))
            self.fade = max(0, self.fade - 14)

        pygame.display.flip()

    # -------------------------------------------------------- main loop
    def run(self):

        running = True

        while running:

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:

                    if self.state == "home":
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key in (pygame.K_1, pygame.K_RETURN):
                            self.start_mode("ai")
                        elif event.key == pygame.K_2:
                            self.start_mode("two")
                        elif event.key == pygame.K_t:
                            self.toggle_theme()

                    elif event.key == pygame.K_ESCAPE:
                        self.go_home()

                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.start()

                    elif event.key == pygame.K_r:
                        self.msg = ""
                        self.new_game(started=True)

                    elif event.key == pygame.K_t:
                        self.toggle_theme()

                    elif event.key == pygame.K_u:
                        self.msg = ""
                        self.undo()

                    elif pygame.K_1 <= event.key <= pygame.K_7:
                        self.human_move(event.key - pygame.K_1)

                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):
                    if self.click(event.pos):
                        running = False

            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App().run()