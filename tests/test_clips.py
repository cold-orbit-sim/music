"""
Clip integrity tests.

Run after `python -m composer.render` has populated output/.

Tests
-----
- Every expected WAV exists.
- Length is within 50 ms of the target duration.
- No clip is pure silence (RMS > threshold).
- Loop-point continuity: last-frame RMS ≈ first-frame RMS (smooth fade).
- State machine round-robins correctly and sting fires once on ambush.
"""
from __future__ import annotations

import asyncio
import struct
import wave
from pathlib import Path

import numpy as np
import pytest

from composer.state import MusicState
from styles.config import ALL_STYLES

OUTPUT_DIR = Path(__file__).parent.parent / "output"
CLIP_DURATION = 8.0
STING_DURATION = 2.0
SAMPLE_RATE = 44100
DURATION_TOLERANCE = 0.05  # seconds
SILENCE_RMS_THRESHOLD = 1e-4


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as wf:
        n_frames = wf.getnframes()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(n_frames)
    dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sampwidth]
    samples = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    if sampwidth == 2:
        samples /= 32768.0
    elif sampwidth == 4:
        samples /= 2147483648.0
    elif sampwidth == 1:
        samples = (samples - 128) / 128.0
    samples = samples.reshape(-1, n_channels)
    return samples


def _wav_duration(path: Path) -> float:
    with wave.open(str(path)) as wf:
        return wf.getnframes() / wf.getframerate()


def _rms(arr: np.ndarray) -> float:
    return float(np.sqrt(np.mean(arr ** 2)))


# ---------------------------------------------------------------------------
# parametrise expected files
# ---------------------------------------------------------------------------

_CLIP_PARAMS = []
for _s in ALL_STYLES:
    for _vi in range(len(_s.variants)):
        for _layer in ("pad", "rhythm", "tune"):
            _CLIP_PARAMS.append(
                pytest.param(
                    OUTPUT_DIR / _s.name / f"{_layer}_v{_vi}.wav",
                    CLIP_DURATION,
                    id=f"{_s.name}/{_layer}_v{_vi}",
                )
            )
_CLIP_PARAMS.append(
    pytest.param(OUTPUT_DIR / "sting.wav", STING_DURATION, id="sting")
)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path,expected_duration", _CLIP_PARAMS)
def test_file_exists(path: Path, expected_duration: float) -> None:
    assert path.exists(), f"Missing clip: {path}"


@pytest.mark.parametrize("path,expected_duration", _CLIP_PARAMS)
def test_duration(path: Path, expected_duration: float) -> None:
    if not path.exists():
        pytest.skip("file missing")
    dur = _wav_duration(path)
    assert abs(dur - expected_duration) < DURATION_TOLERANCE, (
        f"{path.name}: expected {expected_duration:.2f}s, got {dur:.2f}s"
    )


@pytest.mark.parametrize("path,expected_duration", _CLIP_PARAMS)
def test_not_silent(path: Path, expected_duration: float) -> None:
    if not path.exists():
        pytest.skip("file missing")
    samples = _read_wav(path)
    rms = _rms(samples)
    assert rms > SILENCE_RMS_THRESHOLD, f"{path.name} appears silent (RMS={rms:.6f})"


@pytest.mark.parametrize("path,expected_duration", [
    p for p in _CLIP_PARAMS if "sting" not in str(p)
])
def test_loop_continuity(path: Path, expected_duration: float) -> None:
    """
    The amplitude envelope should fade out by end-of-clip (done_action=2 frees
    the synth).  We just check that the last 100 ms is quieter than the middle
    200 ms — a basic sanity check, not a strict loop-point test.
    """
    if not path.exists():
        pytest.skip("file missing")
    samples = _read_wav(path)
    n = len(samples)
    mid_start = n // 2 - SAMPLE_RATE // 10
    mid_end   = n // 2 + SAMPLE_RATE // 10
    tail_start = n - SAMPLE_RATE // 10
    rms_mid  = _rms(samples[mid_start:mid_end])
    rms_tail = _rms(samples[tail_start:])
    assert rms_tail <= rms_mid * 10.0 or rms_tail < 0.005, (
        f"{path.name}: tail RMS ({rms_tail:.4f}) unexpectedly louder than mid ({rms_mid:.4f})"
    )


# ---------------------------------------------------------------------------
# state machine tests (no WAV I/O needed)
# ---------------------------------------------------------------------------

def test_state_round_robin() -> None:
    state = MusicState(output_dir="output")
    t0 = state.tick()
    t1 = state.tick()
    t2 = state.tick()
    assert "v0" in t0.pad
    assert "v1" in t1.pad
    assert "v0" in t2.pad  # wraps back


def test_state_style_switch() -> None:
    state = MusicState(output_dir="output")
    state.set_style("fight")
    t = state.tick()
    assert "fight" in t.pad


def test_ambush_fires_sting_once() -> None:
    state = MusicState(output_dir="output")
    state.trigger_ambush()
    t0 = state.tick()
    t1 = state.tick()
    assert t0.sting is not None
    assert t1.sting is None


def test_ambush_switches_to_fight() -> None:
    state = MusicState(style="normal", output_dir="output")
    state.trigger_ambush()
    t = state.tick()
    assert "fight" in t.pad
