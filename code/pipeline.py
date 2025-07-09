from __future__ import annotations
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT.parent / ".venv" / "Scripts" / "python.exe"
HC = [str(VENV_PYTHON), "-m", "hyperchoron.cli"]


ALL_FLAGS = {
    "resolution", "speed", "volume", "transpose", "invert_key",
    "strum_affinity", "drums", "mc_legal", "max_distance",
    "command_blocks", "minecart_improvements",
}


def hc_args(d: dict[str, str | int | float | bool]) -> list[str]:
    out: list[str] = []
    for k, v in d.items():
        if k not in ALL_FLAGS or v is None:
            continue
        flag = "--" + k.replace("_", "-")
        if isinstance(v, bool):
            if v:
                out.append(flag)
        else:
            out.extend([flag, str(v)])
    return out


def shell(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def fail(msg: str):
    print(msg, file=sys.stderr)
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("midi_file")
    ap.add_argument("--output", "-o", default="output")
    ap.add_argument("--keep-nbs", action="store_true")
    ap.add_argument("--audio-env")
    # pass‑through hyperchoron flags
    for f in ALL_FLAGS:
        flag_name = f"--{f.replace('_','-')}"
        if f in ["mc_legal", "drums", "invert_key", "command_blocks", "minecart_improvements"]:
            # These are boolean flags that should use store_true
            ap.add_argument(flag_name, dest=f, action="store_true")
        else:
            # These are value-based flags
            ap.add_argument(flag_name, dest=f)

    args = ap.parse_args()
    midi = Path(args.midi_file).expanduser().resolve()
    if not midi.exists():
        fail(f"input not found: {midi}")

    outdir = Path(args.output).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    basename = midi.stem

    # Hyperchoron conversion (NBS + CSV + Minecraft formats)
    nbs = outdir / f"{basename}.nbs"
    csv = outdir / f"{basename}.csv"
    nbt = outdir / f"{basename}.nbt"

    # Generate .nbs and .csv files
    for dest in (".nbs", ".csv"):
        cmd = HC + ["-i", str(midi), "-o", str(outdir / f"{basename}{dest}")]
        cmd.extend(hc_args(vars(args)))
        result = shell(cmd)
        if result.returncode:
            fail(result.stderr)
    
    # Generate minecraft-specific .nbt file for web interface
    cmd = HC + ["-i", str(midi), "-o", str(nbt)]
    cmd.extend(hc_args(vars(args)))
    result = shell(cmd)
    if result.returncode:
        fail(result.stderr)

    # Render to flac via render_song.py (optional)
    flac = outdir / f"{basename}.flac"
    render = ROOT / "render_song.py"
    pyexe = "python"
    if args.audio_env:
        venv = Path(args.audio_env)
        pyexe = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

    try:
        result = shell([str(pyexe), str(render), str(nbs), str(flac)])
        if result.returncode:
            print(f"Warning: Audio rendering failed: {result.stderr}", file=sys.stderr)
            print("Note: .nbs and .csv files were created successfully", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Audio rendering failed: {e}", file=sys.stderr)
        print("Note: .nbs and .csv files were created successfully", file=sys.stderr)

    # cleanup
    if not args.keep_nbs and nbs.exists():
        nbs.unlink()

    meta = {
        "display_name": basename,
        "original_file": midi.name,
        "converted_at": datetime.utcnow().isoformat(timespec="seconds").replace(":", "-") + "Z",
        "parameters": {k: v for k, v in vars(args).items() if k in ALL_FLAGS and v is not None},
    }
    (outdir / "metadata.json").write_text(json.dumps(meta, indent=2))
    print("OK")


if __name__ == "__main__":
    main()
