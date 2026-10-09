import os
import random
from math import isqrt

from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Ellipse


# ============================================================
# NUMBER GUESSING CHALLENGE — DARK SHADOW EDITION (V3)
# Range: 1-100 | 5 chances | 5 hint categories
#
# Optional sound files can be placed next to main.py:
#   background.wav
#   correct.wav
#   wrong.wav
#   gameover.wav
#
# This is a Kivy prototype. Android APK packaging is a separate step.
# ============================================================

Window.clearcolor = (0.025, 0.018, 0.055, 1)

BG = (0.025, 0.018, 0.055, 1)
PANEL = (0.085, 0.055, 0.14, 1)
PURPLE = (0.55, 0.20, 1.0, 1)
PURPLE_DARK = (0.22, 0.10, 0.36, 1)
WHITE = (0.96, 0.93, 1.0, 1)
MUTED = (0.72, 0.67, 0.82, 1)
GREEN = (0.20, 1.0, 0.62, 1)
RED = (1.0, 0.27, 0.42, 1)
GOLD = (1.0, 0.78, 0.25, 1)

MIN_NUMBER = 1
MAX_NUMBER = 100
MAX_CHANCES = 5


def is_prime(number):
    if number < 2:
        return False
    for divisor in range(2, isqrt(number) + 1):
        if number % divisor == 0:
            return False
    return True


def digit_sum(number):
    return sum(int(digit) for digit in str(number))


def make_hints(number):
    """Create five truthful hints from the five requested categories."""
    parity = "Even" if number % 2 == 0 else "Odd"
    prime_text = "Prime" if is_prime(number) else "Not prime"

    # Choose a true divisor between 2 and 10 when one exists.
    divisors = [d for d in range(2, 11) if number % d == 0]
    if divisors:
        divisor = random.choice(divisors)
        divisibility = f"The number is divisible by {divisor}."
    else:
        divisibility = "It is not divisible by any number from 2 to 10."

    # Exactly 20 consecutive integers, always within 1..100 and containing number.
    low = max(1, min(number - 9, 81))
    high = low + 19
    if high > 100:
        high = 100
        low = 81

    return [
        f"1. ODD / EVEN: The number is {parity}.",
        f"2. PRIME CHECK: The number is {prime_text}.",
        f"3. DIVISIBILITY: {divisibility}",
        f"4. RANGE: The number is between {low} and {high}.",
        f"5. DIGIT SUM: Its digits add up to {digit_sum(number)}."
    ]


class NeonPanel(BoxLayout):
    """A simple rounded panel widget."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*PANEL)
            self.panel_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(16)]
            )
        self.bind(pos=self._sync_rect, size=self._sync_rect)

    def _sync_rect(self, *_):
        self.panel_rect.pos = self.pos
        self.panel_rect.size = self.size


class NumberGuessingChallenge(App):
    def build(self):
        self.title = "Number Guessing Challenge"
        self.score = 0
        self.best_score = self.load_best_score()
        self.chances_used = 0
        self.secret_number = None
        self.hints = []
        self.restart_event = None
        self.sound_enabled = True
        self.sounds = {}
        self.background_sound = None
        self.load_sounds()

        self.root = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(14), dp(16), dp(14)],
            spacing=dp(10)
        )

        with self.root.canvas.before:
            Color(*BG)
            self.bg_rect = RoundedRectangle(
                pos=self.root.pos, size=self.root.size
            )
        self.root.bind(pos=self._sync_background, size=self._sync_background)

        # Decorative neon dots; subtle pulse animation.
        self.dots = []
        with self.root.canvas.after:
            for i in range(9):
                x = random.uniform(0.05, 0.95)
                y = random.uniform(0.08, 0.92)
                Color(0.45, 0.15, 0.9, 0.30)
                dot = Ellipse(
                    pos=(Window.width * x, Window.height * y),
                    size=(dp(3 + i % 3), dp(3 + i % 3))
                )
                self.dots.append(dot)
        Clock.schedule_interval(self.animate_dots, 1.2)

        self.show_menu()
        return self.root

    def _sync_background(self, *_):
        self.bg_rect.pos = self.root.pos
        self.bg_rect.size = self.root.size

    def animate_dots(self, _dt):
        # Light, low-cost decorative movement.
        for dot in self.dots:
            x, y = dot.pos
            dot.pos = (x, y + random.choice([-1, 0, 1]) * dp(2))
            if dot.pos[1] > Window.height:
                dot.pos = (random.randint(0, max(1, int(Window.width))), 0)

    def load_best_score(self):
        try:
            return int(self.user_data_dir and open(
                os.path.join(self.user_data_dir, "best_score.txt"),
                "r", encoding="utf-8"
            ).read().strip())
        except (OSError, ValueError, TypeError):
            return 0

    def save_best_score(self):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            with open(
                os.path.join(self.user_data_dir, "best_score.txt"),
                "w", encoding="utf-8"
            ) as file:
                file.write(str(self.best_score))
        except OSError:
            pass

    def load_sounds(self):
        for key, filename in {
            "correct": "correct.wav",
            "wrong": "wrong.wav",
            "gameover": "gameover.wav"
        }.items():
            path = os.path.join(os.path.dirname(__file__), filename)
            if os.path.exists(path):
                self.sounds[key] = SoundLoader.load(path)

        music_path = os.path.join(os.path.dirname(__file__), "background.wav")
        if os.path.exists(music_path):
            self.background_sound = SoundLoader.load(music_path)
            if self.background_sound:
                self.background_sound.loop = True
                self.background_sound.volume = 0.25

    def play_sound(self, key):
        if self.sound_enabled and self.sounds.get(key):
            self.sounds[key].stop()
            self.sounds[key].play()

    def start_music(self):
        if self.sound_enabled and self.background_sound:
            self.background_sound.play()

    def stop_music(self):
        if self.background_sound:
            self.background_sound.stop()

    def label(self, text, size=17, color=WHITE, height=None, markup=False):
        widget = Label(
            text=text,
            markup=markup,
            font_size=dp(size),
            color=color,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(height if height is not None else size * 1.7)
        )
        widget.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", (value[0] - dp(8), None))
        )
        return widget

    def button(self, text, callback, color=PURPLE):
        btn = Button(
            text=text,
            font_size=dp(16),
            bold=True,
            color=WHITE,
            size_hint_y=None,
            height=dp(50),
            background_normal="",
            background_down="",
            background_color=color
        )
        btn.bind(on_release=callback)
        btn.bind(on_press=lambda *_: self.button_pulse(btn))
        return btn

    def button_pulse(self, widget):
        Animation.cancel_all(widget)
        original = widget.opacity
        (Animation(opacity=0.72, duration=0.07) +
         Animation(opacity=original, duration=0.12)).start(widget)

    def clear(self):
        if self.restart_event:
            self.restart_event.cancel()
            self.restart_event = None
        self.root.clear_widgets()

    def add_title(self, first, second=None):
        self.root.add_widget(self.label(f"[b]{first}[/b]", 25, WHITE, markup=True))
        if second:
            self.root.add_widget(self.label(f"[b]{second}[/b]", 23, PURPLE, markup=True))

    def show_menu(self, *_):
        self.clear()
        if self.sound_enabled:
            self.start_music()
        self.add_title("NUMBER GUESSING", "CHALLENGE")
        if len(self.root.children) >= 2:
            title_widget = self.root.children[-1]
            pulse = Animation(opacity=0.72, duration=0.8) + Animation(opacity=1, duration=0.8)
            pulse.repeat = True
            pulse.start(title_widget)
        self.root.add_widget(self.label("✦ DARK SHADOW EDITION ✦", 14, PURPLE))
        self.root.add_widget(self.label(
            "Find the secret number from 1 to 100", 16, WHITE, height=40
        ))
        self.root.add_widget(self.label(
            f"BEST SCORE  {self.best_score}", 18, GOLD
        ))
        self.root.add_widget(Widget(size_hint_y=0.2))
        self.root.add_widget(self.button("▶   PLAY GAME", self.start_round))
        sound_text = "♫  SOUND: ON" if self.sound_enabled else "♫  SOUND: OFF"
        self.root.add_widget(self.button(
            sound_text, self.toggle_sound, PURPLE_DARK
        ))
        self.root.add_widget(self.label(
            "5 CHANCES   •   5 HINT TYPES", 13, MUTED, height=30
        ))

    def toggle_sound(self, *_):
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.start_music()
        else:
            self.stop_music()
        self.show_menu()

    def start_round(self, *_):
        self.chances_used = 0
        self.secret_number = random.randint(MIN_NUMBER, MAX_NUMBER)
        self.hints = make_hints(self.secret_number)
        self.show_game()
        self.start_music()

    def show_game(self):
        self.clear()
        self.add_title("NUMBER MYSTERY")
        self.chance_label = self.label("CHANCE 1 OF 5", 17, GOLD)
        self.root.add_widget(self.chance_label)

        self.hints_panel = NeonPanel(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(3),
            size_hint_y=None,
            height=dp(220)
        )
        self.hints_label = self.label("", 14, WHITE, height=190, markup=True)
        self.hints_panel.add_widget(self.hints_label)
        self.root.add_widget(self.hints_panel)

        self.entry = TextInput(
            hint_text="Enter a number (1–100)",
            multiline=False,
            input_filter="int",
            halign="center",
            font_size=dp(22),
            size_hint_y=None,
            height=dp(52),
            background_normal="",
            background_active="",
            background_color=PANEL,
            foreground_color=WHITE,
            cursor_color=PURPLE
        )
        self.entry.bind(on_text_validate=self.check_guess)
        self.root.add_widget(self.entry)

        self.root.add_widget(self.button("⚡  SUBMIT GUESS", self.check_guess))
        self.feedback = self.label("Your mission starts now!", 15, GREEN, height=38)
        self.root.add_widget(self.feedback)
        self.root.add_widget(self.button("⌂  MAIN MENU", self.show_menu, PURPLE_DARK))
        self.update_hint_display()

        self.hints_panel.opacity = 0
        Animation(opacity=1, duration=0.45).start(self.hints_panel)

    def update_hint_display(self):
        next_chance = min(self.chances_used + 1, MAX_CHANCES)
        visible_count = 3 if next_chance <= 3 else next_chance
        self.hints_label.text = (
            "[b]YOUR HINTS[/b]\n\n" +
            "\n".join(self.hints[:visible_count])
        )
        self.chance_label.text = f"CHANCE {next_chance} OF {MAX_CHANCES}"

    def check_guess(self, *_):
        if self.chances_used >= MAX_CHANCES or not hasattr(self, "entry"):
            return

        raw = self.entry.text.strip()
        if not raw:
            self.feedback.text = "Enter a number first."
            self.feedback.color = RED
            return

        guess = int(raw)
        if not MIN_NUMBER <= guess <= MAX_NUMBER:
            self.feedback.text = "Choose a number from 1 to 100."
            self.feedback.color = RED
            return

        self.chances_used += 1
        self.entry.text = ""

        if guess == self.secret_number:
            points = (MAX_CHANCES - self.chances_used + 1) * 10
            self.score += points
            self.best_score = max(self.best_score, self.score)
            self.save_best_score()
            self.play_sound("correct")
            self.show_result(
                True,
                f"Correct! The secret number was {self.secret_number}.\n"
                f"+{points} points!\nTotal score: {self.score}"
            )
            return

        self.play_sound("wrong")
        self.feedback.text = (
            "TOO LOW! Try a higher number."
            if guess < self.secret_number
            else "TOO HIGH! Try a lower number."
        )
        self.feedback.color = RED

        # Shake the feedback text for a wrong answer.
        Animation.cancel_all(self.feedback)
        base_x = self.feedback.x
        (Animation(x=base_x + dp(8), duration=0.05) +
         Animation(x=base_x - dp(8), duration=0.05) +
         Animation(x=base_x + dp(5), duration=0.05) +
         Animation(x=base_x, duration=0.05)).start(self.feedback)

        if self.chances_used >= MAX_CHANCES:
            self.play_sound("gameover")
            self.show_result(
                False,
                f"Round over! The secret number was {self.secret_number}.\n"
                "A new round will start in 4 seconds."
            )
            return

        self.update_hint_display()

    def show_result(self, won, message):
        self.clear()
        if won:
            self.stop_music()
        color = GREEN if won else RED
        title = "[b]VICTORY![/b]" if won else "[b]GAME OVER[/b]"
        title_label = self.label(title, 30, color, markup=True)
        self.root.add_widget(title_label)
        title_label.opacity = 0
        Animation(opacity=1, duration=0.5).start(title_label)

        self.root.add_widget(self.label(message, 18, WHITE, height=110))
        self.root.add_widget(self.label(
            f"SCORE: {self.score}     BEST: {self.best_score}", 17, GOLD
        ))
        self.root.add_widget(self.button("🔄  PLAY NEXT ROUND", self.start_round))
        self.root.add_widget(self.button("⌂  MAIN MENU", self.show_menu, PURPLE_DARK))

        if not won:
            self.restart_event = Clock.schedule_once(self.start_round, 4)


if __name__ == "__main__":
    NumberGuessingChallenge().run()
