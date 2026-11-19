"""
Run (AFTER the first patch):
    python gui/patch_interface_v2.py gui/interface.py

Adds:
  1. Cleaner home title (whole words, no per-letter spacing glitches)
  2. Intro animation: words appear one by one WITH sound
  3. Sound effects (tick, click, disc drop, win jingle) - generated in code, no files needed
  4. "< Back" button inside the game (top of the board) + ESC
  5. New home features: How to Play, About, Sound On/Off
Backup is saved as interface_backup2.py
"""
import os
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "interface.py"
if not os.path.exists(path):
    sys.exit(f"File not found: {path}")

src = open(path, encoding="utf-8").read()
open(os.path.join(os.path.dirname(os.path.abspath(path)), "interface_backup2.py"),
     "w", encoding="utf-8").write(src)


def rep(old, new):
    global src
    n = src.count(old)
    if n != 1:
        sys.exit(f"PATCH FAILED (found {n} matches) for:\n{old[:90]}...")
    src = src.replace(old, new)


# ---------------------------------------------------------------- imports / fonts
rep("import copy\nimport json\n", "import array\nimport copy\nimport json\n")
rep('"segoeui,helvetica,arial,dejavusans"',
    '"segoeui,helveticaneue,helvetica,arial,ubuntu,liberationsans,dejavusans"')

# ---------------------------------------------------------------- init
rep("""        self.home_buttons = self.build_home_buttons()
""", """        self.home_buttons = self.build_home_buttons()
        self.sound_rect = pygame.Rect(u(40), u(30), u(170), u(52))
        self.home_theme_rect = pygame.Rect(WIDTH - u(40) - u(170), u(30), u(170), u(52))
        self.back_rect = pygame.Rect(self.theme_rect.x - u(150), u(30), u(140), u(40))
        self.info_back_rect = pygame.Rect(0, 0, 0, 0)
        self.intro_t0 = time.time()
        self.revealed = 0
        self.init_sound()
""")

# ---------------------------------------------------------------- home buttons (5 now)
rep("""        w, h = u(420), u(80)
        x = WIDTH // 2 - w // 2
        top = u(420)
        return [
            ("ai", pygame.Rect(x, top, w, h), "Play vs AI"),
            ("two", pygame.Rect(x, top + u(100), w, h), "2 Players"),
            ("quit", pygame.Rect(x, top + u(200), w, h), "Quit"),
        ]
""", """        w, h = u(420), u(62)
        x = WIDTH // 2 - w // 2
        top = u(395)
        items = [
            ("ai", "Play vs AI"), ("two", "2 Players"),
            ("howto", "How to Play"), ("about", "About"), ("quit", "Quit"),
        ]
        return [
            (bid, pygame.Rect(x, top + i * u(74), w, h), label)
            for i, (bid, label) in enumerate(items)
        ]
""")

# ---------------------------------------------------------------- sound + new home page
HOWTO = '''HOWTO_LINES = [
    "Drop a disc into a column. Connect 4 in a row to win.",
    "Rows, columns and diagonals all count.",
    "Play vs AI: pick an opponent and a strength on the right.",
    "2 Players: two people take turns on the same screen.",
    "Click a column or press keys 1-7 to drop a disc.",
    "U = undo    R = restart    T = theme    ESC = back to menu",
    "Neural MCTS uses a CNN (policy + value) to guide the search.",
]

ABOUT_LINES = [
    "Mini-AlphaZero: Connect Four with CNN + Monte Carlo Tree Search",
    "",
    "Name: Khadeeja     Roll No: 24-BSCS-29",
    "Instructor: Sir Abdul Rafio",
    "",
    "AI agents: Random, Minimax, Alpha-Beta, Standard MCTS, Neural MCTS",
    "Neural MCTS is trained by self-play (policy head + value head).",
    "GUI: pygame, 9 themes, undo, 2-player mode, sound and animations.",
]


'''
rep("# ------------------------------------------------------------------ app\nclass App:",
    "# ------------------------------------------------------------------ text\n"
    + HOWTO + "# ------------------------------------------------------------------ app\nclass App:")

NEW = '''    # -------------------------------------------------------- sound
    def make_tone(self, notes, vol=0.3):
        rate, fmt, channels = pygame.mixer.get_init()
        if fmt != -16:
            raise RuntimeError("unsupported audio format")
        data = array.array("h")
        for freq, ms in notes:
            n = int(rate * ms / 1000)
            for i in range(n):
                env = min(1.0, i / (rate * 0.005), (n - i) / (rate * 0.03))
                v = int(32767 * vol * env * math.sin(2 * math.pi * freq * i / rate))
                for _ in range(channels):
                    data.append(v)
        return pygame.mixer.Sound(buffer=data.tobytes())

    def init_sound(self):
        self.sound_on = True
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 1, 512)
            self.sounds = {
                "tick": self.make_tone([(988, 55)], 0.25),
                "click": self.make_tone([(660, 40), (880, 50)], 0.25),
                "drop": self.make_tone([(300, 40), (200, 70)], 0.35),
                "win": self.make_tone(
                    [(523, 110), (659, 110), (784, 110), (1047, 260)], 0.3
                ),
            }
        except Exception as error:
            print("Sound disabled:", error)
            self.sounds = {}

    def play(self, name):
        if self.sound_on and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass

    # -------------------------------------------------------- intro + home page
    UI_TIME = 0.4 + 2 * 0.55 + 0.2 + 9 * 0.2 + 0.2

    def intro_time(self):
        return time.time() - self.intro_t0

    def draw_fade_text(self, content, pos, font, color, alpha, anchor="topleft"):
        image = font.render(content, True, color)
        image.set_alpha(int(255 * alpha))
        rect = image.get_rect()
        setattr(rect, anchor, pos)
        self.screen.blit(image, rect)

    def draw_home(self):
        screen = self.screen
        wave = time.time() - self.t0
        now = self.intro_time()

        # Falling translucent discs
        self.layer.fill((0, 0, 0, 0))
        for p in self.particles:
            p["y"] += p["v"]
            if p["y"] > HEIGHT + p["r"]:
                p["y"] = -p["r"]
                p["x"] = random.uniform(0, WIDTH)
            sway = math.sin(wave * 1.5 + p["x"]) * u(12)
            disc(self.layer, PLAYER_COLOR[p["p"]] + (70,),
                 (p["x"] + sway, p["y"]), p["r"])
        screen.blit(self.layer, (0, 0))

        title_words = ["MINI", "ALPHAZERO"]
        sub_words = ["Connect", "Four", "|", "CNN", "+",
                     "Monte", "Carlo", "Tree", "Search"]
        base = 0.4 + 2 * 0.55 + 0.2
        times = [0.4, 0.95] + [base + i * 0.2 for i in range(len(sub_words))]

        # One tick sound per new word
        count = sum(1 for t in times if now >= t)
        if count > self.revealed:
            self.play("tick")
            self.revealed = count

        # Title: two big words appear one after the other
        font = self.f_hero
        gap = font.size(" ")[0]
        widths = [font.size(w)[0] for w in title_words]
        x = WIDTH // 2 - (sum(widths) + gap) // 2
        for i, word in enumerate(title_words):
            a = max(0.0, min(1.0, (now - times[i]) / 0.35))
            if a > 0:
                dy = int((1 - a) * u(40))
                bob = int(math.sin(wave * 2.5 + i * 1.3) * u(6)) if a >= 1 else 0
                self.draw_fade_text(
                    word, (x, u(110) + dy + bob), font,
                    ACCENT if i == 0 else TEXT, a
                )
            x += widths[i] + gap

        # Subtitle: word by word
        font = self.f_norm
        gap = font.size(" ")[0]
        widths = [font.size(w)[0] for w in sub_words]
        x = WIDTH // 2 - (sum(widths) + gap * (len(sub_words) - 1)) // 2
        for i, word in enumerate(sub_words):
            a = max(0.0, min(1.0, (now - times[2 + i]) / 0.25))
            if a > 0:
                self.draw_fade_text(
                    word, (x, u(235) + int((1 - a) * u(14))), font, MUTED, a
                )
            x += widths[i] + gap

        # Discs drop in, then bounce
        for i in range(7):
            e = now - (self.UI_TIME - 0.6 + i * 0.08)
            if e < 0:
                continue
            drop = max(0.0, 0.4 - e) * u(500)
            bounce = abs(math.sin(wave * 2.5 + i * 0.7)) * u(26) if e >= 0.4 else 0
            cx = WIDTH // 2 + (i - 3) * u(80)
            disc(screen, PLAYER_COLOR[1 if i % 2 == 0 else -1],
                 (cx, u(335) - int(drop) - int(bounce)), u(28))

        # Buttons slide in from the left, then pulse
        ready = now >= self.UI_TIME
        mouse = pygame.mouse.get_pos()
        for i, (bid, rect, label) in enumerate(self.home_buttons):
            e = now - (self.UI_TIME + i * 0.1)
            if e < 0:
                continue
            a = min(1.0, e / 0.3)
            hover = ready and rect.collidepoint(mouse)
            grow = u(8) if hover else (int(math.sin(wave * 3 + i) * u(2)) if ready else 0)
            r = rect.inflate(grow * 2, grow).move(-int((1 - a) * u(200)), 0)

            if bid == "ai":
                bg, fg = (GREEN_HOVER if hover else GREEN), WHITE
            elif bid == "two":
                bg, fg = ACCENT, WHITE
            else:
                bg, fg = (BTN_HOVER if hover else BTN), TEXT

            pygame.draw.rect(screen, bg, r, border_radius=u(22))
            if bid not in ("ai", "two"):
                pygame.draw.rect(screen, BORDER, r, 2, border_radius=u(22))
            self.text(label, r.center, self.f_med, fg, "center")

        if ready:
            self.text(
                "1 vs AI  |  2 two players  |  H how to play  |  A about  |  "
                "M sound  |  T theme  |  ESC quit",
                (WIDTH // 2, HEIGHT - u(40)), self.f_small, MUTED, "center"
            )

        self.draw_button(
            self.sound_rect, f"Sound: {'On' if self.sound_on else 'Off'}"
        )
        self.draw_button(self.home_theme_rect, f"Theme: {self.theme}")

    def draw_info(self):
        screen = self.screen
        card = pygame.Rect(u(100), u(110), WIDTH - u(200), HEIGHT - u(250))

        pygame.draw.rect(screen, PANEL_BG, card, border_radius=u(20))
        pygame.draw.rect(screen, PANEL_EDGE, card, 2, border_radius=u(20))

        if self.state == "howto":
            heading, lines = "HOW TO PLAY", HOWTO_LINES
        else:
            heading, lines = "ABOUT", ABOUT_LINES

        self.text(heading, (card.x + u(40), card.y + u(30)), self.f_big, ACCENT)

        y = card.y + u(110)
        for line in lines:
            self.text(line, (card.x + u(40), y), self.f_norm, TEXT)
            y += u(40)

        self.info_back_rect = pygame.Rect(
            card.x + u(40), card.bottom - u(80), u(160), u(54)
        )
        self.draw_button(self.info_back_rect, "< Back")

    def draw_home_old(self):
'''
rep("    def draw_home(self):\n", NEW)

# ---------------------------------------------------------------- sounds in game
rep("""        self.moves.append((col, player))
        self.last_move = (row, col)
""", """        self.moves.append((col, player))
        self.last_move = (row, col)
        self.play("drop")
""")
rep("                    self.spawn_confetti()\n",
    '                    self.spawn_confetti()\n                    self.play("win")\n')

# ---------------------------------------------------------------- click handling
rep("""        if self.theme_rect.collidepoint(pos):
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

        if not self.started and self.start_rect.collidepoint(pos):""",
    """        if self.state == "home":

            if self.home_theme_rect.collidepoint(pos):
                self.toggle_theme()
                return False

            if self.sound_rect.collidepoint(pos):
                self.sound_on = not self.sound_on
                self.play("click")
                return False

            # A click during the intro skips it
            if self.intro_time() < self.UI_TIME:
                self.intro_t0 = time.time() - 100
                return False

            for bid, rect, _ in self.home_buttons:
                if rect.collidepoint(pos):
                    self.play("click")
                    if bid == "quit":
                        return True
                    if bid in ("howto", "about"):
                        self.state = bid
                        self.fade = 255
                    else:
                        self.start_mode(bid)
                    break
            return False

        if self.state in ("howto", "about"):
            if self.info_back_rect.collidepoint(pos):
                self.play("click")
                self.go_home()
            return False

        if self.back_rect.collidepoint(pos):
            self.play("click")
            self.go_home()
            return False

        if self.theme_rect.collidepoint(pos):
            self.toggle_theme()
            return False

        if not self.started and self.start_rect.collidepoint(pos):""")

# ---------------------------------------------------------------- Back button in the game header
rep("""        self.text(label, pill.center, self.f_med, WHITE, "center")

        self.draw_button(self.theme_rect, f"Theme: {self.theme}")""",
    """        self.text(label, pill.center, self.f_med, WHITE, "center")

        self.draw_button(self.theme_rect, f"Theme: {self.theme}")
        self.draw_button(self.back_rect, "< Back")""")

# ---------------------------------------------------------------- draw dispatch
rep("""        if self.state == "home":
            self.draw_home()
        else:""", """        if self.state == "home":
            self.draw_home()
        elif self.state in ("howto", "about"):
            self.draw_info()
        else:""")

# ---------------------------------------------------------------- keys
rep("""                    if self.state == "home":
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key in (pygame.K_1, pygame.K_RETURN):
                            self.start_mode("ai")
                        elif event.key == pygame.K_2:
                            self.start_mode("two")
                        elif event.key == pygame.K_t:
                            self.toggle_theme()
""", """                    if self.state == "home":
                        if self.intro_time() < self.UI_TIME:
                            self.intro_t0 = time.time() - 100   # skip intro
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key in (pygame.K_1, pygame.K_RETURN):
                            self.start_mode("ai")
                        elif event.key == pygame.K_2:
                            self.start_mode("two")
                        elif event.key == pygame.K_h:
                            self.state = "howto"
                            self.fade = 255
                        elif event.key == pygame.K_a:
                            self.state = "about"
                            self.fade = 255
                        elif event.key == pygame.K_m:
                            self.sound_on = not self.sound_on
                        elif event.key == pygame.K_t:
                            self.toggle_theme()

                    elif (self.state in ("howto", "about")
                          and event.key != pygame.K_ESCAPE):
                        pass
""")

open(path, "w", encoding="utf-8").write(src)
print("Done. Backup: interface_backup2.py  |  Updated:", path)