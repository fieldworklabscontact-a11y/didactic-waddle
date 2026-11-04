# NEST — Vercel deployment

This version places the one-page frontend and FastAPI backend in one Vercel project.
The original command-line scripts are included at the repository root and are called
by a thin HTTP adapter in `main.py`.

## Files

- `main.py` — FastAPI endpoints and static frontend mount
- `frontend/` — one-page interface
- `basicmetadatacollector.py` — original collector script
- `extract.py` — original extractor script
- `requirements.txt` — Python dependencies
- `.python-version` — Python 3.12

## Deploy

1. Put the contents of this folder at the root of your GitHub repository.
2. In Vercel, choose **Add New → Project** and import `fieldworklabscontact-a11y/didactic-waddle`.
3. Leave the Framework Preset as **Other** if Vercel does not detect FastAPI automatically.
4. Set the Root Directory to `./` (repository root).
5. Leave Build Command and Output Directory at their defaults. Do not set a custom Start Command.
6. Deploy.

Vercel detects the top-level `main.py` FastAPI app and installs dependencies from `requirements.txt`.
The frontend is served by FastAPI's final static-file mount; API routes are under `/api/`.

## Local run

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.

## Notes

- The two original Python scripts are retained as source files and are not rewritten by the web adapter.
- Uploaded files are handled in temporary storage for each request; the app does not retain uploads.
- Vercel Functions have request-size and execution limits. Large WebM files may need a direct-to-object-storage upload workflow rather than a normal multipart request.
- This is a simple single-user tool. It does not add accounts or persistent file storage.
