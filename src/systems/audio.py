import pygame
import os
from config import SOUNDS_DIR

class AudioManager:
    """
    Central audio controller.
    - SFX: event-driven one-shot sounds (coin, defeat, death, win).
    - BGM: looping background music with independent on/off toggle.
    Missing files are skipped silently so the game never crashes.
    """

    def __init__(self):
        self.sfx_enabled   = True
        self.music_enabled = True
        self._sfx          = {}
        self._current_bgm  = None
        self._sfx_volume   = 0.6
        self._music_volume = 0.5

        # Map logical event name -> candidate filenames (first that exists wins)
        sfx_files = {
            "coin":   ["coin.wav", "coin.mp3", "coin.ogg", "pickup.wav"],
            "defeat": ["defeat.wav", "stomp.wav", "enemy_defeat.wav", "defeat.mp3"],
            "death":  ["death.wav", "death.mp3", "lose_life.wav", "gameover.wav"],
            "win":    ["win.wav", "fanfare.wav", "win.mp3", "level_complete.wav"],
            "jump":   ["jump.wav", "jump.mp3"],
            "power":  ["powerup.wav", "power.wav", "powerup.mp3"],
        }
        for name, candidates in sfx_files.items():
            snd = self._load_sfx(candidates)
            if snd is not None:
                self._sfx[name] = snd

    def _load_sfx(self, candidates):
        for fn in candidates:
            path = os.path.join(SOUNDS_DIR, fn)
            if os.path.exists(path):
                try:
                    s = pygame.mixer.Sound(path)
                    s.set_volume(self._sfx_volume)
                    return s
                except Exception:
                    continue
        return None

    # ── SFX ────────────────────────────────────────────────────────
    def play_sfx(self, name):
        if not self.sfx_enabled:
            return
        snd = self._sfx.get(name)
        if snd is not None:
            try:
                snd.play()
            except Exception:
                pass

    def play_coin(self):   self.play_sfx("coin")
    def play_defeat(self): self.play_sfx("defeat")
    def play_death(self):  self.play_sfx("death")
    def play_win(self):    self.play_sfx("win")
    def play_jump(self):   self.play_sfx("jump")
    def play_power(self):  self.play_sfx("power")

    # ── BGM ────────────────────────────────────────────────────────
    def play_bgm(self, filename, loop=True, start_pos=0.0):
        """Load and play a looping music track if music is enabled."""
        path = os.path.join(SOUNDS_DIR, filename)
        if not os.path.exists(path):
            self._current_bgm = None
            return
        self._current_bgm = filename
        if not self.music_enabled:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            if start_pos > 0:
                try: pygame.mixer.music.set_pos(start_pos)
                except Exception: pass
        except Exception:
            pass

    def stop_bgm(self):
        try: pygame.mixer.music.stop()
        except Exception: pass

    def set_music_enabled(self, enabled):
        """Toggle BGM independently of SFX."""
        self.music_enabled = enabled
        if not enabled:
            self.stop_bgm()
        elif self._current_bgm:
            self.play_bgm(self._current_bgm)

    def toggle_music(self):
        self.set_music_enabled(not self.music_enabled)

    def set_sfx_enabled(self, enabled):
        self.sfx_enabled = enabled
