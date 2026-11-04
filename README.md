# NEST — WEBM EXTRACTER + how to run

## HOW TO RUN: 
Welcome to NEST!

NEST is a web-based tool that allows you to embed files into WebM videos and extract files that have already been embedded.

You don't need to install anything or create an account. Simply open the website in your browser and follow the instructions below.

How to Embed Files into a WebM Video

Open the NEST website.

Select the WebM video you want to use.

Select the file or folder you want to embed inside the video.

Enter a name for your finished WebM file.

Click the Embed or Start Embedding button.

Wait while NEST processes your files. Larger files or folders containing many files may take longer.

When processing finishes, download your newly created WebM file.

How to Extract Embedded Files

Open the NEST website.

Navigate to the Extraction section.

Select the WebM video containing the embedded files.

Click the Extract or Start Extraction button.

Wait for NEST to process the video.

Download the extracted files when processing finishes.

Requirements

A modern web browser.

A WebM video (.webm) for embedding or extraction.

The files or folders you want to embed, if using the embedding feature.

An internet connection.

Important Notes

Only WebM video files are accepted.

Do not close the website while an operation is processing.

Processing time depends on video size and the number and size of the files being handled.

Keep a copy of your original video and files.

Do not upload confidential or sensitive information.

Download and keep your finished files somewhere safe.

Troubleshooting

The operation is taking a long time:
Wait for processing to finish. Large folders can take longer to process.

The website cannot process my video:
Make sure your video is in .webm format.

The operation fails:
Refresh the website and try again. If the problem continues, contact the website owner.

Thank you for using NEST!



## FRONT END PROCCESS

A deliberately small one-page web frontend that invokes the **original Python scripts directly**. The two scripts are copied byte-for-byte into `backend/original/`; the browser does not reimplement their archive logic.

## Architecture

- `frontend/`: static one-page app hosted on Netlify.
- `backend/`: FastAPI bridge hosted as a Python service (Render is configured as the example host).
- `backend/original/basicmetadatacollector.py`: unchanged original collector.
- `backend/original/extract.py`: unchanged original extractor.

The backend saves uploads to a temporary working directory, starts the original script as a subprocess, and answers its existing `input()` prompts through stdin. It does not modify the scripts.

## Deploy the Python backend first

1. Push this project to GitHub.
2. In Render, create a **Web Service** from the repository.
3. Set the service root directory to `backend` and choose Docker as the runtime. `backend/Dockerfile` is included.
4. Deploy and copy the service URL, e.g. `https://nest-python-bridge.onrender.com`.

Or deploy from the `backend` directory using its Dockerfile. The backend exposes `/health`.

## Deploy the frontend to Netlify

1. Import the same GitHub repository into Netlify.
2. Netlify reads `netlify.toml`; its base directory is `frontend` and publish directory is `.`.
3. The included `frontend/config.js` is preconfigured for the Render service name in `render.yaml`: `https://nest-python-bridge.onrender.com`. If Render assigns a different service URL (for example, if that name is already taken), update `window.NEST_API_BASE` in `frontend/config.js` to the exact Render service URL, with no trailing slash.
4. Verify the backend by opening `https://YOUR-RENDER-SERVICE.onrender.com/health`. It should return JSON with `"status":"ok"` and both script checks set to `true`.
5. Deploy/redeploy the Netlify site after confirming the backend URL. Netlify serves the frontend; it does not host the Python API.

## Important note about the original collector (since ai was used for the gui)

The original `basicmetadatacollector.py` is preserved exactly, including its existing central-directory signature check and the `new_local_offset` / `new_localoffset` spelling mismatch. In the current control flow, the signature check breaks out of that loop before the misspelled variable is evaluated. The script still writes an output, but leaves ZIP local-header offsets relative to the ZIP payload; the original extractor is designed to normalize the central-directory pointer and read the ZIP payload as a slice. The unchanged collector and extractor have been smoke-tested together with a sample WebM and payload file; the file round-tripped successfully. This app intentionally does not silently patch or rewrite the scripts.

The original extractor is also executed unchanged. Both operations run on the Python backend, not inside the browser. Uploads are held in temporary server storage for the duration of each request and are not written to a permanent user library.

## Local backend development

```bash
cd backend
python -m venv .venv
# activate the environment, then:
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

For local development, temporarily set `window.NEST_API_BASE = "http://localhost:8000"` in `frontend/config.js` and serve the frontend with any static HTTP server. Restore the Render URL before deploying to Netlify.
