const API = (window.NEST_API_BASE || '').replace(/\/$/, '');
const $ = (id) => document.getElementById(id);
const statusBox = $('status');

function showStatus(title, message, error = false) {
  statusBox.hidden = false;
  statusBox.classList.toggle('error', error);
  $('status-mark').textContent = error ? '!' : '✓';
  $('status-title').textContent = title;
  $('status-message').textContent = message;
}
function setBusy(button, busy, label) {
  button.disabled = busy;
  button.querySelector('span:first-child').textContent = busy ? 'Processing…' : label;
}
function formatSize(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}
function showSelected(input, title, hint, mode = 'single') {
  const files = [...input.files];
  if (!files.length) return;
  $(title).textContent = mode === 'many' ? `${files.length} file${files.length === 1 ? '' : 's'} selected` : files[0].name;
  $(hint).textContent = mode === 'many' ? `${formatSize(files.reduce((n, f) => n + f.size, 0))} total · folder structure retained` : formatSize(files[0].size);
}

$('video-file').addEventListener('change', () => showSelected($('video-file'), 'video-name', 'video-hint'));
$('payload-files').addEventListener('change', () => { if ($('payload-files').files.length) $('payload-folder').value = ''; showPayloadSelection(); });
$('payload-folder').addEventListener('change', () => { if ($('payload-folder').files.length) $('payload-files').value = ''; showPayloadSelection(); });
function selectedPayloadFiles() { return [...($('payload-folder').files.length ? $('payload-folder').files : $('payload-files').files)]; }
function showPayloadSelection() { const files = selectedPayloadFiles(); if (!files.length) return; $('payload-name').textContent = `${files.length} file${files.length === 1 ? '' : 's'} selected`; $('payload-hint').textContent = `${formatSize(files.reduce((n, f) => n + f.size, 0))} total · folder structure retained`; }
$('archive-file').addEventListener('change', () => showSelected($('archive-file'), 'archive-name', 'archive-hint'));

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}
async function readError(response) {
  try {
    const data = await response.json();
    return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || data);
  } catch { return `Request failed (${response.status}).`; }
}
function ensureApi() {
  if (!API || API.includes('YOUR-RENDER-SERVICE')) {
    throw new Error('The Python backend URL has not been configured yet. Set NEST_API_BASE in frontend/config.js after deploying the backend.');
  }
}

$('embed-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const video = $('video-file').files[0];
  const files = selectedPayloadFiles();
  if (!video || !files.length) return showStatus('Missing files', 'Choose a WebM video and at least one payload file.', true);
  const button = $('embed-button');
  setBusy(button, true, 'Generate polyglot');
  showStatus('Running original collector', 'Uploading your files and executing basicmetadatacollector.py…');
  try {
    ensureApi();
    const body = new FormData();
    body.append('video', video, video.name);
    body.append('payload_paths', JSON.stringify(files.map(f => f.webkitRelativePath || f.name)));
    body.append('output_name', $('output-name').value.trim() || 'nested.webm');
    files.forEach(f => body.append('payload_files', f, f.name));
    const response = await fetch(`${API}/api/embed`, { method: 'POST', body });
    if (!response.ok) throw new Error(await readError(response));
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    downloadBlob(blob, match?.[1] || 'nested.webm');
    showStatus('Polyglot generated', 'Your WebM download has started.');
  } catch (error) { showStatus('Embedding failed', error.message, true); }
  finally { setBusy(button, false, 'Generate polyglot'); }
});

$('extract-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const archive = $('archive-file').files[0];
  if (!archive) return showStatus('Missing file', 'Choose a polyglot WebM to extract.', true);
  const button = $('extract-button');
  setBusy(button, true, 'Extract archive');
  showStatus('Running original extractor', 'Uploading the WebM and executing extract.py…');
  try {
    ensureApi();
    const body = new FormData();
    body.append('archive', archive, archive.name);
    const response = await fetch(`${API}/api/extract`, { method: 'POST', body });
    if (!response.ok) throw new Error(await readError(response));
    const blob = await response.blob();
    downloadBlob(blob, 'extracted-files.zip');
    showStatus('Extraction complete', 'Your extracted files have been packaged into a ZIP download.');
  } catch (error) { showStatus('Extraction failed', error.message, true); }
  finally { setBusy(button, false, 'Extract archive'); }
});
