# Run: python render_song.py in.nbs out.flac within .venv-audio
from __future__ import annotations

import argparse
from pathlib import Path

import pynbs
from nbswave import SongRenderer


def render_audio(
    song_path: Path,
    output_path: Path,
    default_sound_path: Path = Path("sounds"),
    custom_sound_path: Path | None = None,
    fmt: str = "flac",
    sample_rate: int = 44_100,
    channels: int = 1,
    bit_depth: int = 16,
    target_bitrate: int = 320,
    ignore_missing_instruments: bool = False,
) -> None:
    song = pynbs.read(song_path)
    renderer = SongRenderer(song, str(default_sound_path))
    if custom_sound_path:
        renderer.load_instruments(str(custom_sound_path))
    track = renderer.mix_song()

    params: dict = {
        "format": fmt,
        "sample_width": bit_depth // 8,
        "frame_rate": sample_rate,
        "channels": channels,
    }
    if fmt.lower() not in {"wav", "flac"}:
        params["target_bitrate"] = target_bitrate

    track.save(str(output_path), **params)
    print(f"Rendered: {output_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("infile", type=Path)
    p.add_argument("outfile", type=Path)
    p.add_argument("--sounds", type=Path, default="sounds")
    p.add_argument("--custom-sounds", type=Path)
    p.add_argument("--format", default="flac")
    p.add_argument("--sample-rate", type=int, default=44100)
    p.add_argument("--channels", type=int, default=1)
    p.add_argument("--bit-depth", type=int, default=16)
    p.add_argument("--target-bitrate", type=int, default=320)
    args = p.parse_args()

    render_audio(
        args.infile,
        args.outfile,
        args.sounds,
        args.custom_sounds,
        args.format,
        args.sample_rate,
        args.channels,
        args.bit_depth,
        args.target_bitrate,
    )
