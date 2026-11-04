from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "original"
COLLECTOR = SCRIPTS / "basicmetadatacollector.py"
EXTRACTOR = SCRIPTS / "extract.py"

app = FastAPI(title="NEST Python bridge", version="1.0.0")
allowed = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed if allowed != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def run_original(script: Path, answers: str, cwd: Path) -> subprocess.CompletedProcess:
    if not script.is_file():
        raise HTTPException(500, f"Original script not found: {script.name}")
    try:
        return subprocess.run(
            [sys.executable, str(script)],
            input=answers,
            text=True,
            capture_output=True,
            cwd=cwd,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "The operation took longer than five minutes and was stopped.")


@app.get("/health")
def health():
    return {"status": "ok", "scripts": {
        "embed": COLLECTOR.exists(),
        "extract": EXTRACTOR.exists(),
    }}


@app.post("/api/embed")
async def embed(
    video: UploadFile = File(...),
    payload_files: List[UploadFile] = File(...),
    payload_paths: str = Form(...),
    output_name: str = Form("nested.webm"),
):
    if not video.filename or not video.filename.lower().endswith(".webm"):
        raise HTTPException(400, "Choose a .webm video file.")
    try:
        paths = json.loads(payload_paths)
    except Exception:
        raise HTTPException(400, "Invalid payload file path list.")
    if len(paths) != len(payload_files) or not payload_files:
        raise HTTPException(400, "Choose at least one file to embed.")

    safe_name = Path(output_name).name.strip() or "nested.webm"
    if not safe_name.lower().endswith(".webm"):
        safe_name += ".webm"

    with tempfile.TemporaryDirectory(prefix="nest-embed-") as tmp:
        work = Path(tmp)
        video_path = work / Path(video.filename).name
        video_path.write_bytes(await video.read())
        payload_dir = work / "payload"
        payload_dir.mkdir()
        for upload, relative in zip(payload_files, paths):
            relative_path = Path(str(relative).replace("\\", "/"))
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise HTTPException(400, "Invalid uploaded file path.")
            destination = payload_dir / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(await upload.read())
        output_path = work / safe_name
        # The script is run unchanged. Its three input() prompts are answered here.
        result = run_original(COLLECTOR, f"{payload_dir}\n{video_path}\n{safe_name}\ny\n", work)
        if result.returncode != 0 or not output_path.exists():
            details = (result.stdout + "\n" + result.stderr).strip()
            raise HTTPException(500, "The original collector script failed.\n" + details[-6000:])
        return Response(content=output_path.read_bytes(), media_type="video/webm", headers={"Content-Disposition": f'attachment; filename="{safe_name}"'})


@app.post("/api/extract")
async def extract(archive: UploadFile = File(...)):
    if not archive.filename:
        raise HTTPException(400, "Choose a polyglot WebM file.")
    with tempfile.TemporaryDirectory(prefix="nest-extract-") as tmp:
        work = Path(tmp)
        input_path = work / Path(archive.filename).name
        input_path.write_bytes(await archive.read())
        output_dir = work / "extracted"
        result = run_original(EXTRACTOR, f"{input_path}\n{output_dir}\n", work)
        if result.returncode != 0 or not output_dir.exists():
            details = (result.stdout + "\n" + result.stderr).strip()
            raise HTTPException(500, "The original extractor script failed.\n" + details[-6000:])
        zip_path = work / "extracted-files.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in output_dir.rglob("*"):
                if item.is_file():
                    zf.write(item, item.relative_to(output_dir))
        return Response(content=zip_path.read_bytes(), media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="extracted-files.zip"'})
