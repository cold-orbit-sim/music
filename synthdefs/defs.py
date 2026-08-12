"""
SynthDef builders for all four layers: pad, rhythm, tune, sting.

Each builder returns a supriya.SynthDef.  Parameters are floats so the
Score API can drive them directly.
"""
from __future__ import annotations

from supriya import SynthDef
from supriya.ugens import (
    BPF,
    HPF,
    LPF,
    RLPF,
    Decay2,
    EnvGen,
    Impulse,
    LeakDC,
    LFNoise1,
    LFNoise2,
    LFPulse,
    LFTri,
    Line,
    Out,
    PinkNoise,
    Ringz,
    SinOsc,
    VarSaw,
    WhiteNoise,
)
from supriya.ugens.envelopes import Envelope
from supriya import SynthDefBuilder


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _build_pad(name: str) -> SynthDef:
    """
    Slowly evolving detuned saw pad filtered with a drifting LPF.

    Controls
    --------
    out        : bus index
    freq       : fundamental Hz
    detune     : detune in Hz between two oscillators (default 1.5)
    amp        : output amplitude (default 0.18)
    cutoff     : LPF cutoff Hz (default 800)
    rq         : RLPF reciprocal Q (default 0.4)
    atk        : envelope attack in seconds (default 0.4)
    duration   : total duration in seconds
    """
    with SynthDefBuilder(
        out=0,
        freq=220.0,
        detune=1.5,
        amp=0.18,
        cutoff=800.0,
        rq=0.4,
        atk=0.4,
        duration=8.0,
    ) as b:
        env = EnvGen.kr(
            envelope=Envelope.linen(
                attack_time=b["atk"],
                sustain_time=b["duration"] - b["atk"] - 0.3,
                release_time=0.3,
                level=1.0,
            ),
            done_action=2,
        )
        drift = LFNoise1.kr(frequency=0.3) * 0.5
        osc1 = VarSaw.ar(frequency=b["freq"] + b["detune"] + drift, width=0.4)
        osc2 = VarSaw.ar(frequency=b["freq"] - b["detune"] - drift, width=0.6)
        mix = (osc1 + osc2) * 0.5
        fc = b["cutoff"] + LFNoise2.kr(frequency=0.15) * (b["cutoff"] * 0.4)
        filt = RLPF.ar(source=mix, frequency=fc, reciprocal_of_q=b["rq"])
        filt = LeakDC.ar(source=filt)
        sig = filt * env * b["amp"]
        Out.ar(bus=b["out"], source=[sig, sig])
    return b.build(name=name)


def _build_rhythm(name: str) -> SynthDef:
    """
    Kick + hi-hat pattern driven by impulse trains.

    Controls
    --------
    out        : bus index
    bpm        : tempo in BPM (default 60)
    amp        : output amplitude (default 0.5)
    hat_freq   : hi-hat pattern density Hz (default 4 = 16th notes at 60 BPM)
    duration   : total duration in seconds
    """
    with SynthDefBuilder(
        out=0,
        bpm=60.0,
        amp=0.5,
        hat_freq=4.0,
        duration=8.0,
    ) as b:
        env = EnvGen.kr(
            envelope=Envelope.linen(
                attack_time=0.01,
                sustain_time=b["duration"] - 0.02,
                release_time=0.01,
                level=1.0,
            ),
            done_action=2,
        )
        beat_hz = b["bpm"] / 60.0

        # --- kick ---
        kick_trig = Impulse.ar(frequency=beat_hz)
        kick_env = Decay2.ar(source=kick_trig, attack_time=0.004, decay_time=0.35)
        kick_pitch = kick_env * 80 + 50
        kick_sig = SinOsc.ar(frequency=kick_pitch) * kick_env * 0.9

        # --- hi-hat (noise burst) ---
        hat_trig = Impulse.ar(frequency=b["hat_freq"])
        hat_env = Decay2.ar(source=hat_trig, attack_time=0.001, decay_time=0.06)
        hat_sig = HPF.ar(source=WhiteNoise.ar(), frequency=8000.0) * hat_env * 0.3

        mix = (kick_sig + hat_sig) * env * b["amp"]
        Out.ar(bus=b["out"], source=[mix, mix])
    return b.build(name=name)


def _build_tune(name: str) -> SynthDef:
    """
    Monophonic arpeggiated square-ish wave melody.

    Controls
    --------
    out        : bus index
    freq0..3   : four arpeggio pitches in Hz
    bpm        : tempo in BPM (default 60)
    amp        : output amplitude (default 0.22)
    duration   : total duration in seconds
    """
    with SynthDefBuilder(
        out=0,
        freq0=220.0,
        freq1=261.6,
        freq2=329.6,
        freq3=392.0,
        bpm=60.0,
        amp=0.22,
        duration=8.0,
    ) as b:
        env_full = EnvGen.kr(
            envelope=Envelope.linen(
                attack_time=0.01,
                sustain_time=b["duration"] - 0.02,
                release_time=0.01,
                level=1.0,
            ),
            done_action=2,
        )
        beat_hz = b["bpm"] / 60.0
        step_hz = beat_hz * 2.0

        trig = Impulse.ar(frequency=step_hz)
        note_env = Decay2.ar(source=trig, attack_time=0.005, decay_time=0.18)

        # Cycle through freq0..3 using four phase-offset pulse trains
        sel0 = LFPulse.kr(frequency=step_hz / 4.0, initial_phase=0.0, width=0.25)
        sel1 = LFPulse.kr(frequency=step_hz / 4.0, initial_phase=0.25, width=0.25)
        sel2 = LFPulse.kr(frequency=step_hz / 4.0, initial_phase=0.5, width=0.25)
        sel3 = LFPulse.kr(frequency=step_hz / 4.0, initial_phase=0.75, width=0.25)

        freq = (
            b["freq0"] * sel0
            + b["freq1"] * sel1
            + b["freq2"] * sel2
            + b["freq3"] * sel3
        )

        osc = LFTri.ar(frequency=freq + 0.5)
        filt = BPF.ar(source=osc, frequency=freq * 2, reciprocal_of_q=0.5)
        sig = filt * note_env * env_full * b["amp"]
        Out.ar(bus=b["out"], source=[sig, sig])
    return b.build(name=name)


def _build_sting(name: str) -> SynthDef:
    """
    One-shot ambush sting: rising noise sweep + resonant ping.

    Controls
    --------
    out        : bus index
    amp        : output amplitude (default 0.7)
    duration   : sting length in seconds (default 2.0)
    """
    with SynthDefBuilder(
        out=0,
        amp=0.7,
        duration=2.0,
    ) as b:
        dur = b["duration"]
        env = EnvGen.kr(
            envelope=Envelope.linen(
                attack_time=0.01,
                sustain_time=dur - 0.31,
                release_time=0.3,
                level=1.0,
            ),
            done_action=2,
        )
        sweep = Line.kr(start=200.0, stop=4000.0, duration=dur)
        noise = BPF.ar(
            source=PinkNoise.ar(),
            frequency=sweep,
            reciprocal_of_q=0.2,
        )
        ping = Ringz.ar(
            source=WhiteNoise.ar() * Impulse.ar(frequency=0.5),
            frequency=880.0,
            decay_time=0.4,
        )
        mix = (noise * 0.6 + ping * 0.5) * env * b["amp"]
        Out.ar(bus=b["out"], source=[mix, mix])
    return b.build(name=name)


# ---------------------------------------------------------------------------
# public registry
# ---------------------------------------------------------------------------

PAD_DEF: SynthDef = _build_pad("co_pad")
RHYTHM_DEF: SynthDef = _build_rhythm("co_rhythm")
TUNE_DEF: SynthDef = _build_tune("co_tune")
STING_DEF: SynthDef = _build_sting("co_sting")

ALL_DEFS: tuple[SynthDef, ...] = (PAD_DEF, RHYTHM_DEF, TUNE_DEF, STING_DEF)
