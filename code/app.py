from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# configuration
ROOT          = Path(__file__).resolve().parent
UPLOADS       = ROOT / "uploads"
OUTPUTS       = ROOT / "output"
PLAYLISTS_DIR = ROOT / "playlists"
SPADIR        = ROOT / "static"
AUDIO_ENV     = ROOT.parent / ".venv-audio"
MAX_BATCH     = 20
MAX_SIZE_MB   = 50
ALLOWED_EXT   = {"mid", "midi", "nbs", "org", "zip", "csv"}

for d in (UPLOADS, OUTPUTS, PLAYLISTS_DIR, SPADIR):
    d.mkdir(exist_ok=True)

# helpers
def ok(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def timestamp() -> str:
    return datetime.utcnow().isoformat(timespec="seconds").replace(":", "-") + "Z"


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2))


def run_pipeline(infile: Path,
                 outdir: Path,
                 keep_nbs: bool,
                 extra: dict[str, Any] | None = None,
                 audio_env: Path | None = None) -> tuple[bool, str]:

    audio_env = audio_env or AUDIO_ENV
    
    # Use the same Python executable that's running this Flask app
    import sys
    python_exe = sys.executable
    print(f"Using Python executable: {python_exe}")
    
    cmd = [
        python_exe, str(ROOT / "pipeline.py"),
        str(infile),
        "--output", str(outdir),
    ]
    if keep_nbs:
        cmd.append("--keep-nbs")
    if audio_env:
        cmd.extend(["--audio-env", str(audio_env)])

    # pass through recognised hyperchoron parameters
    if extra:
        for key, val in extra.items():
            if isinstance(val, bool) and val:
                cmd.append(f"--{key.replace('_', '-')}")
            elif isinstance(val, (int, float, str)):
                cmd.extend([f"--{key.replace('_', '-')}", str(val)])

    print(f"Running command: {' '.join(cmd)}")
    proc = subprocess.run(cmd, text=True, capture_output=True)
    print(f"Command result: returncode={proc.returncode}")
    print(f"STDOUT: {proc.stdout}")
    print(f"STDERR: {proc.stderr}")
    return proc.returncode == 0, proc.stdout + "\n" + proc.stderr


def list_songs() -> list[dict]:
    songs: list[dict] = []
    for d in OUTPUTS.iterdir():
        if not d.is_dir():
            continue
        meta = load_json(d / "metadata.json", {})
        songs.append({
            "id": d.name,
            "name": meta.get("display_name", d.name),
            "created": meta.get("converted_at", timestamp()),
            "files": sorted(p.as_posix() for p in d.glob("*") if p.is_file()),
        })
    return sorted(songs, key=lambda s: s["created"], reverse=True)


def list_playlists() -> list[dict]:
    pls: list[dict] = []
    for p in PLAYLISTS_DIR.glob("*.json"):
        data = load_json(p, {})
        if not data:
            continue
        pls.append({
            "id": p.stem,
            "name": data.get("name", p.stem),
            "created": data.get("created", timestamp()),
            "songs": data.get("songs", []),
        })
    return sorted(pls, key=lambda x: x["created"], reverse=True)

app = Flask(__name__, static_folder=str(SPADIR), static_url_path="")
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = MAX_SIZE_MB * 1024 * 1024

@app.route("/")
def spa() -> Any:
    return send_from_directory(SPADIR, "index.html")

@app.get("/api/songs")
def api_songs():
    return jsonify(list_songs())


@app.delete("/api/songs/<sid>")
def api_song_delete(sid: str):
    target = OUTPUTS / sid
    if target.is_dir():
        shutil.rmtree(target)
        # also remove from any playlist
        for p in PLAYLISTS_DIR.glob("*.json"):
            data = load_json(p, {})
            if "songs" in data and sid in data["songs"]:
                data["songs"].remove(sid)
                save_json(p, data)
        return "", 204
    return jsonify({"error": "Song not found"}), 404


@app.put("/api/songs/<sid>")
def api_song_rename(sid: str):
    new_name = request.json.get("name", "").strip()
    if not new_name:
        return jsonify({"error": "Name required"}), 400
    target = OUTPUTS / sid
    if not target.is_dir():
        return jsonify({"error": "Song not found"}), 404
    meta_path = target / "metadata.json"
    meta = load_json(meta_path, {})
    meta["display_name"] = new_name
    save_json(meta_path, meta)
    return "", 204


# playlist API
@app.get("/api/playlists")
def api_playlists():
    return jsonify(list_playlists())


@app.post("/api/playlists")
def api_playlist_create():
    body = request.json
    name = body.get("name", "").strip()
    songs = list(dict.fromkeys(body.get("songs", [])))  # unique, preserve order
    if not name or not songs:
        return jsonify({"error": "Name and songs required"}), 400
    payload = {
        "name": name,
        "created": timestamp(),
        "songs": songs,
    }
    save_json(PLAYLISTS_DIR / f"{secure_filename(name)}.json", payload)
    return "", 201


@app.delete("/api/playlists/<pid>")
def api_playlist_delete(pid: str):
    f = PLAYLISTS_DIR / f"{pid}.json"
    if f.exists():
        f.unlink()
        return "", 204
    return jsonify({"error": "Playlist not found"}), 404


# upload & conversion
@app.post("/api/upload")
def api_upload():
    """
    Expects a multipart/form‑data request with:

      files            … up to 20 file fields
      global_params    … JSON string with master settings
      per_file_params  … JSON string {filename: {...}}

    Response: list of {"file": originalName, "ok": bool, "log": str}
    """
    files = request.files.getlist("files")
    if not files or len(files) > MAX_BATCH:
        return jsonify({"error": "Attach 1‒20 files"}), 400

    try:
        global_params = json.loads(request.form.get("global_params", "{}"))
        per_file = json.loads(request.form.get("per_file_params", "{}"))
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in parameters"}), 400

    results = []

    for f in files:
        if not ok(f.filename):
            results.append({"file": f.filename, "ok": False,
                            "log": "unsupported extension"})
            continue

        safe = secure_filename(f.filename)
        temp = UPLOADS / f"{timestamp()}_{safe}"
        f.save(temp)

        outdir = OUTPUTS / Path(safe).stem
        merged: dict[str, Any] = {**global_params, **per_file.get(f.filename, {})}
        keep_nbs = bool(merged.pop("keep_nbs", False))

        success, log = run_pipeline(temp, outdir, keep_nbs, merged)
        temp.unlink(missing_ok=True)
        results.append({"file": f.filename, "ok": success, "log": log})

    return jsonify(results), 207


# convert but don't store
@app.post("/api/convert-ephemeral")
def api_ephemeral():
    """
    Converts one file, returns ZIP of minecraft‑friendly outputs only.
    --mc‑legal flag is forced TRUE and present in the UI only here.
    """
    try:
        print("=== EPHEMERAL CONVERT DEBUG ===")
        f = request.files.get("file")
        print(f"File received: {f}")
        print(f"File filename: {f.filename if f else 'None'}")
        
        if not f or not ok(f.filename):
            print(f"Bad file error: f={f}, filename={f.filename if f else 'None'}")
            return jsonify({"error": "Bad file"}), 400

        params_str = request.form.get("params", "{}")
        print(f"Params string: {params_str}")
        params = json.loads(params_str)
        print(f"Parsed params: {params}")
        
        params["mc_legal"] = True
        safe = secure_filename(f.filename)
        print(f"Safe filename: {safe}")

        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"Using temp directory: {tmpdir}")
            tmpdir = Path(tmpdir)
            infile = tmpdir / safe
            print(f"Input file path: {infile}")
            f.save(infile)
            print(f"File saved successfully: {infile.exists()}")

            outdir = tmpdir / "out"
            outdir.mkdir()
            print(f"Output directory created: {outdir}")

            print("Starting pipeline conversion...")
            success, log = run_pipeline(infile, outdir,
                                        keep_nbs=True,
                                        extra=params)
            print(f"Pipeline result: success={success}")
            print(f"Pipeline log: {log}")
            
            if not success:
                print("Pipeline conversion failed")
                return jsonify({"error": "Conversion failed", "log": log}), 500

            wanted = [p for p in outdir.rglob("*")
                      if p.suffix.lower() in {".mcfunction", ".litematic", ".nbt"}]
            print(f"Found minecraft files: {[p.name for p in wanted]}")

            if not wanted:
                print("No minecraft outputs found")
                return jsonify({"error": "No minecraft outputs produced"}), 422

            from zipfile import ZipFile
            mem = io.BytesIO()
            with ZipFile(mem, "w") as z:
                for p in wanted:
                    z.write(p, p.name)
            mem.seek(0)
            print("ZIP file created successfully")
            
            return send_file(
                mem,
                mimetype="application/zip",
                as_attachment=True,
                download_name=f"{Path(safe).stem}_minecraft_outputs.zip",
            )
    except Exception as e:
        print(f"ERROR in ephemeral convert: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal error: {str(e)}"}), 500


# download endpoint for songs
@app.post("/api/download")
def api_download():
    song_id = request.form.get("song_id")
    if not song_id:
        return jsonify({"error": "Song ID required"}), 400
    
    song_dir = OUTPUTS / song_id
    if not song_dir.is_dir():
        return jsonify({"error": "Song not found"}), 404
    
    # Get all files in the song directory
    files = [f for f in song_dir.rglob("*") if f.is_file()]
    if not files:
        return jsonify({"error": "No files found"}), 404
    
    # If only one file, send it directly
    if len(files) == 1:
        return send_file(files[0], as_attachment=True)
    
    # Multiple files - create a zip
    from zipfile import ZipFile
    mem = io.BytesIO()
    with ZipFile(mem, "w") as z:
        for f in files:
            # Use relative path within the song directory for the archive
            arcname = f.relative_to(song_dir)
            z.write(f, arcname)
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{song_id}_files.zip"
    )


# health check
@app.get("/api/status")
def api_status():
    return jsonify({
        "status": "online",
        "songs": len(list_songs()),
        "playlists": len(list_playlists()),
        "timestamp": timestamp(),
    })


# static assets fallback
@app.route("/<path:path>")
def spa_fallback(path: str):
    target = SPADIR / path
    if target.exists():
        return send_from_directory(SPADIR, path)
    return send_from_directory(SPADIR, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
