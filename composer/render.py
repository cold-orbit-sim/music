"""
Batch renderer: produces all clip WAVs for every style/layer/variant
plus the ambush sting.

Output layout
-------------
output/
  <style>/
    pad_v0.wav
    pad_v1.wav
    rhythm_v0.wav
    rhythm_v1.wav
    tune_v0.wav
    tune_v1.wav
  sting.wav

Usage
-----
    python -m composer.render [--output-dir OUTPUT_DIR] [--duration SECS]
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from supriya import HeaderFormat, SampleFormat, Score
from supriya.scsynth import Options

from styles.config import ALL_STYLES
from synthdefs.defs import PAD_DEF, RHYTHM_DEF, TUNE_DEF, STING_DEF

_STEREO_OPTIONS = Options(output_bus_channel_count=2)

CLIP_DURATION: float = 8.0
STING_DURATION: float = 2.0
SAMPLE_RATE: int = 44100
_HEADER = HeaderFormat.WAV
_SAMPLE = SampleFormat.INT16


async def _render_score(
    score: Score,
    path: Path,
    duration: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    await score.render(
        output_file_path=path,
        duration=duration,
        sample_rate=SAMPLE_RATE,
        header_format=_HEADER,
        sample_format=_SAMPLE,
        options=_STEREO_OPTIONS,
    )
    print(f"  written {path}")


async def render_clip(
    layer: str,
    params: dict,
    path: Path,
    duration: float = CLIP_DURATION,
) -> None:
    synthdef = {"pad": PAD_DEF, "rhythm": RHYTHM_DEF, "tune": TUNE_DEF}[layer]
    score = Score()
    with score.at(0):
        score.add_synthdefs(synthdef)
        score.add_synth(synthdef, duration=duration, **params)
    await _render_score(score, path, duration)


async def render_sting(path: Path) -> None:
    score = Score()
    with score.at(0):
        score.add_synthdefs(STING_DEF)
        score.add_synth(STING_DEF, duration=STING_DURATION)
    await _render_score(score, path, STING_DURATION)


async def render_all(output_dir: Path, duration: float = CLIP_DURATION) -> None:
    tasks: list = []

    for style in ALL_STYLES:
        for vi, variant in enumerate(style.variants):
            for layer in ("pad", "rhythm", "tune"):
                params = variant[layer]
                path = output_dir / style.name / f"{layer}_v{vi}.wav"
                tasks.append(render_clip(layer, params, path, duration))

    tasks.append(render_sting(output_dir / "sting.wav"))

    await asyncio.gather(*tasks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Cold Orbit music clips")
    parser.add_argument("--output-dir", default="output", help="Root output directory")
    parser.add_argument(
        "--duration", type=float, default=CLIP_DURATION, help="Clip duration in seconds"
    )
    args = parser.parse_args()
    asyncio.run(render_all(Path(args.output_dir), args.duration))


if __name__ == "__main__":
    main()
