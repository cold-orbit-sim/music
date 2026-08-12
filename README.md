# Cold Orbit – Adaptive Music System

Procedurally rendered adaptive music for the Cold Orbit spaceship simulator.
All audio is generated offline (Non-Realtime / NRT) via **SuperCollider scsynth**
driven by **Supriya** (Python). No DAW or audio assets are required.

## Architecture

```
output/
  <style>/          # normal | fight | stealth | trading
    pad_v0.wav      # slow evolving pad, variant 0
    pad_v1.wav      # slow evolving pad, variant 1
    rhythm_v0.wav   # kick + hi-hat pattern, variant 0
    rhythm_v1.wav   # kick + hi-hat pattern, variant 1
    tune_v0.wav     # arpeggiated melody, variant 0
    tune_v1.wav     # arpeggiated melody, variant 1
  sting.wav         # one-shot ambush sting
```

Each clip is **8 seconds, 44100 Hz, 16-bit stereo WAV** (sting is 2 s).
The game engine plays the three layers (pad / rhythm / tune) concurrently and
swaps clips round-robin every 8 s. Crossfading is the engine's responsibility.

### Styles and keys

| Style   | Root | Scale         | BPM |
|---------|------|---------------|-----|
| normal  | A3   | Natural minor | 60  |
| fight   | D4   | Phrygian      | 90  |
| stealth | G3   | Dorian        | 50  |
| trading | C4   | Lydian        | 70  |

## Prerequisites

- **Python ≥ 3.14**
- **scsynth** 3.13+ on `$PATH` (install SuperCollider)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Render clips

```bash
python -m composer.render            # writes to output/
python -m composer.render --output-dir /path/to/game/music
```

## Run tests

Tests require a populated `output/` directory.

```bash
pytest
```

Tests check:
- Every expected WAV exists
- Duration within 50 ms of target
- No clip is silent
- Amplitude envelope fades by clip end
- State machine round-robin and ambush behaviour

## Integrating with the game engine

```python
from composer.state import MusicState

state = MusicState(output_dir="/path/to/output")

# Normal game loop tick (call every 8 s)
clip = state.tick()
engine.play(clip.pad)
engine.play(clip.rhythm)
engine.play(clip.tune)

# Change music style
state.set_style("stealth")

# Ambush event
state.trigger_ambush()          # next tick fires the sting + switches to fight
clip = state.tick()
if clip.sting:
    engine.play_one_shot(clip.sting)
```

## File map

```
synthdefs/defs.py      – SynthDef builders (pad, rhythm, tune, sting)
styles/config.py       – Per-style musical params (key, scale, BPM, variants)
composer/render.py     – Async NRT batch renderer CLI
composer/state.py      – Round-robin + ambush state machine
tests/test_clips.py    – Pytest suite
pyproject.toml         – Build config and test settings
```
