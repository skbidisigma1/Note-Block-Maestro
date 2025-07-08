#!/usr/bin/env python3
"""Fixed version of render_song.py that works around nbswave API bug."""

import argparse
import pynbs
from nbswave import SongRenderer
from pydub import AudioSegment

def render_audio_fixed(
    song_path: str,
    output_path: str,
    default_sound_path: str = "sounds",
    custom_sound_path: str = None,
    format: str = "wav",
    sample_rate: int = 44100,
    channels: int = 2,
    bit_depth: int = 16,
    target_bitrate: int = 320,
    target_size: int = None,
    headroom_db: float = 0.0,
    ignore_missing_instruments: bool = False,
) -> None:
    """Render NBS file to audio, working around nbswave API bug."""
    song = pynbs.read(song_path)
    renderer = SongRenderer(song, default_sound_path)
    
    if custom_sound_path:
        renderer.load_instruments(custom_sound_path)
    
    # Mix the song
    track = renderer.mix_song()
    
    # Only pass parameters that Track.save() actually accepts
    save_params = {
        'format': format,
        'sample_width': bit_depth // 8,
        'frame_rate': sample_rate,
        'channels': channels,
        'target_size': target_size,
    }
    
    # Only add target_bitrate for compressed formats
    if format.lower() not in ['flac', 'wav']:
        save_params['target_bitrate'] = target_bitrate
    
    track.save(output_path, **save_params)
    
    # Apply headroom via post-processing if requested
    # Note: Currently disabled due to nbswave/pydub compatibility issues
    if headroom_db < 0:
        print(f"Note: Headroom adjustment ({headroom_db}dB) requested but disabled due to library conflicts.")
        print("For audio production, consider applying headroom using external tools like FFmpeg:")
        print(f"  ffmpeg -i {output_path} -af 'volume={headroom_db}dB' output_with_headroom.{format}")
    
    print(f"Audio rendered to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render NBS file to audio")
    parser.add_argument("infile", help="Input NBS file")
    parser.add_argument("outfile", help="Output audio file")
    parser.add_argument("--sounds", default="sounds", help="Default sounds directory")
    parser.add_argument("--custom-sounds", help="Custom sounds directory/zip")
    parser.add_argument("--format", default="flac", help="Output format (wav, flac, mp3)")
    parser.add_argument("--sample-rate", type=int, default=44100, help="Sample rate")
    parser.add_argument("--channels", type=int, default=2, help="Number of channels")
    parser.add_argument("--bit-depth", type=int, default=16, help="Bit depth")
    parser.add_argument("--target-bitrate", type=int, default=320, help="Target bitrate for compressed formats")
    parser.add_argument("--headroom", type=float, default=0.0, help="Headroom in dB (e.g. -0.1 for -0.1dBFS, currently informational only)")
    parser.add_argument("--ignore-missing", action="store_true", help="Ignore missing instruments")
    
    args = parser.parse_args()
    
    render_audio_fixed(
        args.infile,
        args.outfile,
        args.sounds,
        args.custom_sounds,
        args.format,
        args.sample_rate,
        args.channels,
        args.bit_depth,
        args.target_bitrate,
        args.headroom,
        ignore_missing_instruments=args.ignore_missing
    )
