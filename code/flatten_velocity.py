import sys
from pathlib import Path
import mido

def flatten_vel(in_path: Path) -> Path:
    mid = mido.MidiFile(in_path)
    for track in mid.tracks:
        for msg in track:
            if msg.type == "note_on":
                msg.velocity = 127
    out_path = in_path.with_stem(in_path.stem + "_flattened")
    mid.save(out_path)
    return out_path

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python flatten_velocity.py <input.mid>")
        sys.exit(1)
    out = flatten_vel(Path(sys.argv[1]))
    print(f"Saved: {out}")