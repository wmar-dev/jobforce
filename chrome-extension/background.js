/**
 * Background service worker — MV3.
 * Receives CAPTURE_JOB trigger from popup, injects content script,
 * collects job data, and POSTs to the Jobforce backend.
 */

const API_BASE = "http://localhost:8000";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "TRIGGER_CAPTURE") {
    handleCapture().then(sendResponse).catch((err) =>
      sendResponse({ ok: false, error: String(err) })
    );
    return true; // async
  }

  if (message.type === "CHECK_STATUS") {
    checkBackendStatus().then(sendResponse).catch(() =>
      sendResponse({ running: false })
    );
    return true;
  }
});

async function handleCapture() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return { ok: false, error: "No active tab" };

  // Ensure content script is injected
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });
  } catch (_) {
    // Already injected — ignore
  }

  // Request job data from content script
  let contentResponse;
  try {
    contentResponse = await chrome.tabs.sendMessage(tab.id, { type: "CAPTURE_JOB" });
  } catch (err) {
    return { ok: false, error: `Content script error: ${err}` };
  }

  if (!contentResponse?.ok) {
    return { ok: false, error: contentResponse?.error || "Extraction failed" };
  }

  const jobData = contentResponse.data;
  if (!jobData.title || !jobData.company_name) {
    return { ok: false, error: "Could not extract job title or company from this page." };
  }

  // POST to backend
  let resp;
  try {
    resp = await fetch(`${API_BASE}/api/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(jobData),
    });
  } catch (_) {
    // Backend not reachable
    await setBadge("✗", "#ef4444");
    await chrome.storage.local.set({ last_error: "backend_offline" });
    return { ok: false, error: "backend_offline" };
  }

  const result = await resp.json();

  if (resp.status === 201) {
    await setBadge("✓", "#10b981");
    await chrome.storage.local.set({
      last_ingested_url: jobData.source_url,
      last_ingested_title: jobData.title,
      last_error: null,
    });
    return { ok: true, duplicate: false, job: result };
  }

  if (resp.status === 409) {
    await setBadge("~", "#f59e0b");
    return { ok: true, duplicate: true, job: result };
  }

  return { ok: false, error: `Backend error: ${resp.status}` };
}

async function checkBackendStatus() {
  try {
    const resp = await fetch(`${API_BASE}/docs`, { method: "HEAD" });
    return { running: resp.ok };
  } catch (_) {
    return { running: false };
  }
}

async function setBadge(text, color) {
  await chrome.action.setBadgeText({ text });
  await chrome.action.setBadgeBackgroundColor({ color });
  // Clear badge after 3 seconds
  setTimeout(() => chrome.action.setBadgeText({ text: "" }), 3000);
}
