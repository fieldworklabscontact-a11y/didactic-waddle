from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
COLLECTOR = ROOT / "basicmetadatacollector.py"
EXTRACTOR = ROOT / "extract.py"

app = FastAPI(title="NEST", docs_url=None, redoc_url=None)


def _safe_filename(name: str, fallback: str) -> str:
    name = Path(name or fallback).name
    if not name or name in {".", ".."}:
        return fallback
    return name


@app.get("/api/health")
def health():
    return {"ok": True, "service": "NEST"}


@app.post("/api/embed")
async def embed(
    video: Annotated[UploadFile, File()],
    payload_files: Annotated[list[UploadFile], File()],
    payload_paths: Annotated[str, Form()] = "[]",
    output_name: Annotated[str, Form()] = "nested.webm",
):
    if not video.filename or not video.filename.lower().endswith(".webm"):
        raise HTTPException(400, "Choose a WebM video.")
    if not payload_files:
        raise HTTPException(400, "Choose a file or folder to embed.")

    try:
        paths = json.loads(payload_paths)
        if not isinstance(paths, list) or len(paths) != len(payload_files):
            raise ValueError
    except Exception:
        paths = [f.filename or f"file-{i}" for i, f in enumerate(payload_files)]

    output_name = _safe_filename(output_name, "nested.webm")
    if not output_name.lower().endswith(".webm"):
        output_name += ".webm"

    with tempfile.TemporaryDirectory(prefix="nest-") as temp:
        work = Path(temp)
        video_path = work / "source.webm"
        video_path.write_bytes(await video.read())

        # A single ordinary file is passed as a file. Multiple files or a selected
        # directory are reconstructed into a directory for the original CLI script.
        folder_mode = len(payload_files) > 1 or any("/" in str(p) or "\\" in str(p) for p in paths)
        if folder_mode:
            payload_path = work / "payload"
            payload_path.mkdir()
        else:
            payload_path = work / _safe_filename(str(paths[0]), "payload.bin")

        for i, upload in enumerate(payload_files):
            rel = Path(str(paths[i]).replace("\\", "/"))
            if rel.is_absolute() or ".." in rel.parts:
                raise HTTPException(400, "Invalid folder path in upload.")
            target = (payload_path / rel) if folder_mode else payload_path
            if folder_mode:
                target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(await upload.read())

        output_path = work / output_name
        stdin = f"{payload_path}\n{video_path}\n{output_path}\ny\n"
        try:
            result = subprocess.run(
                [sys.executable, str(COLLECTOR)],
                input=stdin,
                text=True,
                capture_output=True,
                cwd=work,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "Embedding took too long.")
        if result.returncode != 0 or not output_path.exists():
            detail = (result.stderr or result.stdout or "The original collector exited without producing an output file.").strip()
            raise HTTPException(500, detail[-2500:])
        data = output_path.read_bytes()

    return Response(
        content=data,
        media_type="video/webm",
        headers={"Content-Disposition": f'attachment; filename="{output_name}"'},
    )


@app.post("/api/extract")
async def extract(video: Annotated[UploadFile, File()]):
    if not video.filename or not video.filename.lower().endswith(".webm"):
        raise HTTPException(400, "Choose a WebM file.")
    with tempfile.TemporaryDirectory(prefix="nest-") as temp:
        work = Path(temp)
        video_path = work / "input.webm"
        video_path.write_bytes(await video.read())
        output_dir = work / "extracted"
        stdin = f"{video_path}\n{output_dir}\n"
        try:
            result = subprocess.run(
                [sys.executable, str(EXTRACTOR)],
                input=stdin,
                text=True,
                capture_output=True,
                cwd=work,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "Extraction took too long.")
        if not output_dir.exists() or not any(output_dir.iterdir()):
            detail = (result.stderr or result.stdout or "No files were extracted.").strip()
            raise HTTPException(400, detail[-2500:])

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in output_dir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(output_dir).as_posix())
        archive.seek(0)
        return Response(
            content=archive.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="nest-extracted.zip"'},
        )


# Keep the static mount last so /api routes take precedence.
app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="frontend")
