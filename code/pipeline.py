from __future__ import annotations
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
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
    ap.add_argument("input_file", help="Input file (MIDI, NBS, CSV, ORG, or ZIP)")
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
    input_file = Path(args.input_file).expanduser().resolve()
    if not input_file.exists():
        fail(f"input not found: {input_file}")

    outdir = Path(args.output).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    basename = input_file.stem

    # Hyperchoron conversion (NBS + CSV + Minecraft formats)
    nbs = outdir / f"{basename}.nbs"
    csv = outdir / f"{basename}.csv"
    nbt = outdir / f"{basename}.nbt"
    mcfunction = outdir / f"{basename}.mcfunction"
    litematic = outdir / f"{basename}.litematic"

    # Generate .nbs and .csv files
    for dest in (".nbs", ".csv"):
        cmd = HC + ["-i", str(input_file), "-o", str(outdir / f"{basename}{dest}")]
        cmd.extend(hc_args(vars(args)))
        result = shell(cmd)
        if result.returncode:
            fail(result.stderr)
    
    # Generate minecraft-specific formats for web interface
    for minecraft_format in (nbt, mcfunction, litematic):
        cmd = HC + ["-i", str(input_file), "-o", str(minecraft_format)]
        cmd.extend(hc_args(vars(args)))
        result = shell(cmd)
        if result.returncode:
            print(f"Warning: Failed to generate {minecraft_format.suffix} format: {result.stderr}", file=sys.stderr)
            # Don't fail completely if one format fails, continue with others

    # Render to flac via render_song.py (optional)
    flac = outdir / f"{basename}.flac"
    render = ROOT / "render_song.py"
    pyexe = "python"
    
    # Auto-detect audio environment or use specified one
    if args.audio_env:
        venv = Path(args.audio_env)
        pyexe = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    else:
        # Try to auto-detect .venv-audio in parent directory
        auto_audio_env = ROOT.parent / ".venv-audio"
        if auto_audio_env.exists():
            pyexe = auto_audio_env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            print(f"Auto-detected audio environment: {auto_audio_env}", file=sys.stderr)

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
        "original_file": input_file.name,
        "converted_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(":", "-").replace("+00:00", "Z"),
        "parameters": {k: v for k, v in vars(args).items() if k in ALL_FLAGS and v is not None},
    }
    (outdir / "metadata.json").write_text(json.dumps(meta, indent=2))
    print("OK")


if __name__ == "__main__":
    main()
