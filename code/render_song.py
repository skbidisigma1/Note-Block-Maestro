import argparse
from nbswave import render_audio

parser = argparse.ArgumentParser()
parser.add_argument("infile", help="Input .nbs file")
parser.add_argument("outfile", help="Output audio file")
parser.add_argument("--format", default="flac", help="Output format (flac, wav, etc.)")
parser.add_argument("--sounds", default="sounds/", help="Custom sounds folder")
parser.add_argument("--ignore-missing", action="store_true", help="Ignore missing instruments")

args = parser.parse_args()

render_audio(
    args.infile,
    args.outfile,
    format=args.format,
    custom_sound_path=args.sounds,
    ignore_missing_instruments=args.ignore_missing,
)