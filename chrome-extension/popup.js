const dot = document.getElementById("dot");
const statusText = document.getElementById("status-text");
const captureBtn = document.getElementById("capture-btn");
const resultDiv = document.getElementById("result");
const lastUrlDiv = document.getElementById("last-url");

async function init() {
  // Check backend status
  chrome.runtime.sendMessage({ type: "CHECK_STATUS" }, (resp) => {
    if (resp?.running) {
      dot.className = "dot online";
      statusText.textContent = "Backend running";
      captureBtn.disabled = false;
    } else {
      dot.className = "dot offline";
      statusText.textContent = "Backend offline — run: cd backend && make dev";
      captureBtn.disabled = true;
    }
  });

  // Show last captured URL
  chrome.storage.local.get(["last_ingested_url", "last_ingested_title"], (data) => {
    if (data.last_ingested_url) {
      lastUrlDiv.textContent = `Last: ${data.last_ingested_title || data.last_ingested_url}`;
    }
  });
}

captureBtn.addEventListener("click", () => {
  captureBtn.disabled = true;
  captureBtn.textContent = "Capturing...";
  resultDiv.style.display = "none";

  chrome.runtime.sendMessage({ type: "TRIGGER_CAPTURE" }, (resp) => {
    captureBtn.disabled = false;
    captureBtn.textContent = "📥 Capture This Job";

    if (resp?.error === "backend_offline") {
      showResult("error", "Backend is not running.\nStart it with: cd backend && make dev");
      dot.className = "dot offline";
      statusText.textContent = "Backend offline";
      return;
    }

    if (!resp?.ok) {
      showResult("error", resp?.error || "Capture failed");
      return;
    }

    if (resp.duplicate) {
      showResult("duplicate", "Already saved — this job is in your board.");
    } else {
      showResult("success", `✓ Saved: ${resp.job?.id ? `Job #${resp.job.id}` : "Job captured"}`);
    }
  });
});

function showResult(type, message) {
  resultDiv.className = `result ${type}`;
  resultDiv.textContent = message;
  resultDiv.style.display = "block";
}

init();
