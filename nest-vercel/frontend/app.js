const tabs = document.querySelectorAll(".tab");
const panels = {embed: document.getElementById("embed-panel"), extract: document.getElementById("extract-panel")};
tabs.forEach(tab => tab.addEventListener("click", () => {
  tabs.forEach(t => t.classList.toggle("active", t === tab));
  Object.entries(panels).forEach(([name, panel]) => panel.classList.toggle("active", name === tab.dataset.tab));
  setResult("Ready when you are.", "Choose an operation to begin.", "—");
}));

function setResult(title, message, mark = "—") {
  document.getElementById("result-title").textContent = title;
  document.getElementById("result-message").textContent = message;
  document.querySelector(".result-mark").textContent = mark;
}
async function submitForm(form, button, endpoint, makeData, fallbackName) {
  button.disabled = true;
  button.querySelector("span").textContent = "Working…";
  setResult("Processing request", "The original Python script is running.", "↻");
  try {
    const response = await fetch(endpoint, {method:"POST", body:makeData()});
    if (!response.ok) {
      let message = "Request failed.";
      try { const body = await response.json(); message = body.detail || message; } catch {}
      throw new Error(message);
    }
    const blob = await response.blob();
    const disposition = response.headers.get("content-disposition") || "";
    const match = disposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : fallbackName;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    setResult("Complete", `${filename} was generated and downloaded.`, "✓");
  } catch (error) {
    setResult("Could not complete", error.message, "!");
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = endpoint.endsWith("embed") ? "Build nested WebM" : "Extract ZIP archive";
  }
}
document.getElementById("embed-form").addEventListener("submit", event => {
  event.preventDefault();
  const individualFiles = [...document.getElementById("payload").files];
  const folderFiles = [...document.getElementById("payload-folder").files];
  const files = folderFiles.length ? folderFiles : individualFiles;
  const carrier = document.getElementById("carrier").files[0];
  if (!files.length || !carrier) return;
  const data = new FormData();
  files.forEach(file => data.append("payload_files", file, file.webkitRelativePath || file.name));
  data.append("payload_paths", JSON.stringify(files.map(file => file.webkitRelativePath || file.name)));
  data.append("video", carrier);
  data.append("output_name", document.getElementById("output-name").value || "nested.webm");
  submitForm(event.currentTarget, event.currentTarget.querySelector("button"), "/api/embed", () => data, "nested.webm");
});
document.getElementById("extract-form").addEventListener("submit", event => {
  event.preventDefault();
  const video = document.getElementById("nested-video").files[0];
  if (!video) return;
  const data = new FormData(); data.append("video", video);
  submitForm(event.currentTarget, event.currentTarget.querySelector("button"), "/api/extract", () => data, "nest-extracted.zip");
});
