import argparse
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description, cwd=None):
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error: {e}")
        if e.stdout:
            print(f"  Stdout: {e.stdout}")
        if e.stderr:
            print(f"  Stderr: {e.stderr}")
        return False

def convert_midi_to_formats(midi_path, output_dir):
    midi_path = Path(midi_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    base_name = midi_path.stem
    
    # Convert to NBS
    nbs_path = output_dir / f"{base_name}.nbs"
    cmd = f'hyperchoron -i "{midi_path}" -o "{nbs_path}"'
    if not run_command(cmd, f"Converting {midi_path.name} to NBS"):
        return None, None, None
    
    # Convert to CSV
    csv_path = output_dir / f"{base_name}.csv"
    cmd = f'hyperchoron -i "{midi_path}" -o "{csv_path}"'
    if not run_command(cmd, f"Converting {midi_path.name} to CSV"):
        return nbs_path, None, None
    
    # Convert to JSON
    json_path = None # TODO: add json metadata export
    
    return nbs_path, csv_path, json_path

def render_audio(nbs_path, output_dir, audio_env_path):
    """Render NBS to FLAC using the audio environment."""
    nbs_path = Path(nbs_path)
    output_dir = Path(output_dir)
    
    base_name = nbs_path.stem
    flac_path = output_dir / f"{base_name}.flac"
    
    if sys.platform == "win32":
        python_exe = audio_env_path / "Scripts" / "python.exe"
    else:
        python_exe = audio_env_path / "bin" / "python"
    render_script = Path(__file__).parent / "render_song.py"
    sounds_dir = Path(__file__).parent / "sounds"
    
    cmd = [
        str(python_exe),
        str(render_script),
        str(nbs_path),
        str(flac_path),
    ]
    
    if run_command(cmd, f"Rendering {nbs_path.name} to FLAC"):
        return flac_path
    return None

def main():
    parser = argparse.ArgumentParser(description="Note Block Maestro - MIDI to NBS/CSV/JSON/FLAC pipeline")
    parser.add_argument("midi_file", help="Input MIDI file")
    parser.add_argument("-o", "--output", default="output", help="Output directory (default: output)")
    parser.add_argument("--audio-env", help="Path to audio environment (default: .venv-audio)")
    parser.add_argument("--keep-nbs", action="store_true", help="Keep NBS file (default: replace with FLAC)")
    
    args = parser.parse_args()
    
    midi_path = Path(args.midi_file)
    if not midi_path.exists():
        print(f"Error: MIDI file not found: {midi_path}")
        sys.exit(1)
    
    output_dir = Path(args.output)
    
    if args.audio_env:
        audio_env_path = Path(args.audio_env)
    else:
        audio_env_path = Path(__file__).parent.parent / ".venv-audio"
    
    if not audio_env_path.exists():
        print(f"Error: Audio environment not found: {audio_env_path}")
        print("Run: python -m venv .venv-audio")
        print("Then: .venv-audio\\Scripts\\pip install nbswave numpy==1.26.4 pynbs==0.4.2 pydub audioop-lts")
        sys.exit(1)
    
    print(f"Processing: {midi_path.name}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Step 1: Convert MIDI to formats
    print("Step 1: Converting MIDI to NBS/CSV/JSON...")
    nbs_path, csv_path, json_path = convert_midi_to_formats(midi_path, output_dir)
    
    if not nbs_path:
        print("Failed to convert to NBS format")
        sys.exit(1)
    
    # Step 2: Render audio
    print("\nStep 2: Rendering NBS to FLAC...")
    flac_path = render_audio(nbs_path, output_dir, audio_env_path)
    
    if not flac_path:
        print("Failed to render audio")
        sys.exit(1)
    
    # Step 3: Remove NBS file if not keeping it
    if not args.keep_nbs and nbs_path.exists():
        print(f"\nRemoving NBS file: {nbs_path}")
        nbs_path.unlink()
    
    # Summary
    print("\n" + "="*50)
    print("Pipeline completed successfully!")
    print("="*50)
    
    outputs = []
    if flac_path and flac_path.exists():
        outputs.append(f"AUDIO: {flac_path}")
    if csv_path and csv_path.exists():
        outputs.append(f"CSV: {csv_path}")
    if args.keep_nbs and nbs_path and nbs_path.exists():
        outputs.append(f"NBS: {nbs_path}")
    
    for output in outputs:
        print(f"  {output}")

if __name__ == "__main__":
    main()
