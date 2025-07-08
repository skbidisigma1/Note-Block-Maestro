#!/usr/bin/env python3
"""
Simple wrapper for Note Block Maestro pipeline
Converts any MIDI file to FLAC + CSV with minimal setup
"""

import sys
import argparse
from pathlib import Path
from pipeline import main as pipeline_main

def main():
    if len(sys.argv) < 2:
        print("Note Block Maestro - MIDI to Audio Pipeline")
        print()
        print("Usage:")
        print("  python convert.py <midi_file>")
        print("  python convert.py <midi_file> --output <directory>")
        print()
        print("Examples:")
        print("  python convert.py song.mid")
        print("  python convert.py song.mid --output ./exports")
        print()
        print("Output formats:")
        print("  🎵 FLAC audio for playback")
        print("  📊 CSV data for visualization")
        print()
        sys.exit(1)
    
    # Simple argument handling - just pass through to main pipeline
    sys.argv[0] = "pipeline.py"  # Pretend we're calling pipeline.py
    pipeline_main()

if __name__ == "__main__":
    main()
