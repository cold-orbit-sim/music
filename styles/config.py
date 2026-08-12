"""
Per-style musical configuration.

Each style defines:
  - root_hz     : root pitch in Hz
  - scale       : list of semitone intervals from root (one octave)
  - bpm         : tempo
  - hat_freq    : hi-hat density in Hz (beats-per-second multiples)
  - variants    : list of variant dicts, one per clip variant
                  Each variant overrides pad/rhythm/tune synth params.

Variants are indexed 0..N-1.  render.py iterates over them to produce
  output/<style>/<layer>_v<n>.wav
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


def _midi_to_hz(midi: float) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def _scale_degrees(root_midi: float, intervals: list[int], octave: int = 0) -> list[float]:
    base = root_midi + octave * 12
    return [_midi_to_hz(base + i) for i in intervals]


# Semitone interval sets
MINOR_PENTA   = [0, 3, 5, 7, 10]           # 1 b3 4 5 b7
NATURAL_MINOR = [0, 2, 3, 5, 7, 8, 10]     # Aeolian
DORIAN        = [0, 2, 3, 5, 7, 9, 10]
PHRYGIAN      = [0, 1, 3, 5, 7, 8, 10]
LYDIAN        = [0, 2, 4, 6, 7, 9, 11]


@dataclass
class StyleConfig:
    name: str
    root_midi: float
    scale: list[int]
    bpm: float
    hat_freq: float
    variants: list[dict[str, Any]]


def _arp4(pitches: list[float], offset: int = 0) -> dict[str, float]:
    p = pitches
    n = len(p)
    return {
        "freq0": p[(offset + 0) % n],
        "freq1": p[(offset + 1) % n],
        "freq2": p[(offset + 2) % n],
        "freq3": p[(offset + 3) % n],
    }


# ---------------------------------------------------------------------------
# normal  —  A natural minor, relaxed cruise
# ---------------------------------------------------------------------------
_normal_root = 57.0  # A3
_normal_pitches = _scale_degrees(_normal_root, NATURAL_MINOR)

NORMAL = StyleConfig(
    name="normal",
    root_midi=_normal_root,
    scale=NATURAL_MINOR,
    bpm=60.0,
    hat_freq=4.0,
    variants=[
        {
            "pad":    {"freq": _normal_pitches[0], "cutoff": 700.0, "rq": 0.45, "detune": 1.2},
            "rhythm": {"bpm": 60.0, "hat_freq": 4.0, "amp": 0.4},
            "tune":   {**_arp4(_normal_pitches, 0), "bpm": 60.0, "amp": 0.20},
        },
        {
            "pad":    {"freq": _normal_pitches[2], "cutoff": 600.0, "rq": 0.35, "detune": 1.8},
            "rhythm": {"bpm": 60.0, "hat_freq": 2.0, "amp": 0.35},
            "tune":   {**_arp4(_normal_pitches, 3), "bpm": 60.0, "amp": 0.18},
        },
    ],
)


# ---------------------------------------------------------------------------
# fight  —  D Phrygian, aggressive, fast hats
# ---------------------------------------------------------------------------
_fight_root = 62.0  # D4
_fight_pitches = _scale_degrees(_fight_root, PHRYGIAN)

FIGHT = StyleConfig(
    name="fight",
    root_midi=_fight_root,
    scale=PHRYGIAN,
    bpm=90.0,
    hat_freq=8.0,
    variants=[
        {
            "pad":    {"freq": _fight_pitches[0], "cutoff": 1200.0, "rq": 0.6, "detune": 2.5},
            "rhythm": {"bpm": 90.0, "hat_freq": 8.0, "amp": 0.65},
            "tune":   {**_arp4(_fight_pitches, 0), "bpm": 90.0, "amp": 0.28},
        },
        {
            "pad":    {"freq": _fight_pitches[4], "cutoff": 1400.0, "rq": 0.7, "detune": 3.0},
            "rhythm": {"bpm": 90.0, "hat_freq": 6.0, "amp": 0.60},
            "tune":   {**_arp4(_fight_pitches, 2), "bpm": 90.0, "amp": 0.25},
        },
    ],
)


# ---------------------------------------------------------------------------
# stealth  —  G Dorian, slow, sparse hats
# ---------------------------------------------------------------------------
_stealth_root = 55.0  # G3
_stealth_pitches = _scale_degrees(_stealth_root, DORIAN)

STEALTH = StyleConfig(
    name="stealth",
    root_midi=_stealth_root,
    scale=DORIAN,
    bpm=50.0,
    hat_freq=2.0,
    variants=[
        {
            "pad":    {"freq": _stealth_pitches[0], "cutoff": 450.0, "rq": 0.25, "detune": 0.8, "amp": 0.12},
            "rhythm": {"bpm": 50.0, "hat_freq": 2.0, "amp": 0.25},
            "tune":   {**_arp4(_stealth_pitches, 0), "bpm": 50.0, "amp": 0.14},
        },
        {
            "pad":    {"freq": _stealth_pitches[3], "cutoff": 380.0, "rq": 0.20, "detune": 1.0, "amp": 0.10},
            "rhythm": {"bpm": 50.0, "hat_freq": 1.0, "amp": 0.20},
            "tune":   {**_arp4(_stealth_pitches, 4), "bpm": 50.0, "amp": 0.12},
        },
    ],
)


# ---------------------------------------------------------------------------
# trading  —  C Lydian, bright, upbeat
# ---------------------------------------------------------------------------
_trading_root = 60.0  # C4
_trading_pitches = _scale_degrees(_trading_root, LYDIAN)

TRADING = StyleConfig(
    name="trading",
    root_midi=_trading_root,
    scale=LYDIAN,
    bpm=70.0,
    hat_freq=4.0,
    variants=[
        {
            "pad":    {"freq": _trading_pitches[0], "cutoff": 1000.0, "rq": 0.5, "detune": 1.0},
            "rhythm": {"bpm": 70.0, "hat_freq": 4.0, "amp": 0.45},
            "tune":   {**_arp4(_trading_pitches, 0), "bpm": 70.0, "amp": 0.22},
        },
        {
            "pad":    {"freq": _trading_pitches[2], "cutoff": 1100.0, "rq": 0.55, "detune": 1.4},
            "rhythm": {"bpm": 70.0, "hat_freq": 4.0, "amp": 0.42},
            "tune":   {**_arp4(_trading_pitches, 2), "bpm": 70.0, "amp": 0.20},
        },
    ],
)


ALL_STYLES: tuple[StyleConfig, ...] = (NORMAL, FIGHT, STEALTH, TRADING)
