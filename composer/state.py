"""
Adaptive music state machine for Cold Orbit.

Usage (in game loop or CLI demo):
    from composer.state import MusicState
    state = MusicState()
    clip = state.tick()          # returns ClipSelection each 8-second tick
    state.trigger_ambush()       # switches style to fight + queues sting
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from styles.config import ALL_STYLES, StyleConfig

Style = Literal["normal", "fight", "stealth", "trading"]
Layer = Literal["pad", "rhythm", "tune"]

_STYLE_MAP: dict[str, StyleConfig] = {s.name: s for s in ALL_STYLES}


@dataclass
class ClipSelection:
    """Files the game engine should start playing this tick."""
    pad: str
    rhythm: str
    tune: str
    sting: str | None = None


@dataclass
class MusicState:
    """
    Round-robin adaptive music state machine.

    Attributes
    ----------
    style       : current style name
    _indices    : per-style round-robin cursors
    _ambush     : True for one tick after trigger_ambush(); causes sting to fire
    output_dir  : root dir for pre-rendered WAV files
    """
    style: Style = "normal"
    output_dir: str = "output"
    _indices: dict[str, int] = field(default_factory=lambda: {s.name: 0 for s in ALL_STYLES})
    _ambush: bool = False

    def set_style(self, style: Style) -> None:
        self.style = style

    def trigger_ambush(self) -> None:
        """Switch immediately to fight style and arm the sting for the next tick."""
        self.style = "fight"
        self._ambush = True

    def tick(self) -> ClipSelection:
        """
        Advance one 8-second tick and return the clip filenames to play.
        Cycles through variants round-robin within the current style.
        """
        cfg = _STYLE_MAP[self.style]
        idx = self._indices[self.style]
        n = len(cfg.variants)

        base = f"{self.output_dir}/{self.style}"
        selection = ClipSelection(
            pad=f"{base}/pad_v{idx}.wav",
            rhythm=f"{base}/rhythm_v{idx}.wav",
            tune=f"{base}/tune_v{idx}.wav",
            sting=f"{self.output_dir}/sting.wav" if self._ambush else None,
        )

        self._indices[self.style] = (idx + 1) % n
        self._ambush = False
        return selection
