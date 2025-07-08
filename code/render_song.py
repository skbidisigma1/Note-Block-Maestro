# note: this has to be run in the .venv-audio environment
import argparse
import pynbs
from nbswave import SongRenderer

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
    ignore_missing_instruments: bool = False,
) -> None:
    song = pynbs.read(song_path)
    renderer = SongRenderer(song, default_sound_path)
    
    if custom_sound_path:
        renderer.load_instruments(custom_sound_path)
    
    track = renderer.mix_song()
    
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
    
    print(f"Audio rendered to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render NBS file to audio")
    parser.add_argument("infile", help="Input NBS file")
    parser.add_argument("outfile", help="Output audio file")
    parser.add_argument("--sounds", default="sounds", help="Default sounds directory")
    parser.add_argument("--custom-sounds", help="Custom sounds directory/zip")
    parser.add_argument("--format", default="flac", help="Output format (wav, flac, mp3)")
    parser.add_argument("--sample-rate", type=int, default=44100, help="Sample rate")
    parser.add_argument("--channels", type=int, default=1, help="Number of channels")
    parser.add_argument("--bit-depth", type=int, default=16, help="Bit depth")
    parser.add_argument("--target-bitrate", type=int, default=320, help="Target bitrate for compressed formats")
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
        ignore_missing_instruments=args.ignore_missing
    )
