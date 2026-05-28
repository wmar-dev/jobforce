/**
 * Content script — runs in every page context.
 * Listens for CAPTURE_JOB messages from the background service worker,
 * extracts structured job data from the DOM, and replies.
 */

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type !== "CAPTURE_JOB") return;

  try {
    const data = extractJobData();
    sendResponse({ ok: true, data });
  } catch (err) {
    sendResponse({ ok: false, error: String(err) });
  }
  return true; // keep channel open for async sendResponse
});

function extractJobData() {
  const source_url = window.location.href;
  const html = document.documentElement.outerHTML;

  // Best-effort extraction — works on most job boards
  const title =
    document.querySelector('h1')?.innerText?.trim() ||
    document.title?.replace(/\s*[-|].*$/, "").trim() ||
    "";

  const company_name =
    document.querySelector('[data-company], .company-name, .employer-name')
      ?.innerText?.trim() ||
    document.querySelector('meta[property="og:site_name"]')?.content ||
    "";

  const location =
    document.querySelector('[data-location], .job-location, .location')
      ?.innerText?.trim() ||
    document.querySelector('meta[name="job:location"]')?.content ||
    null;

  // Extract role type from common patterns
  const bodyText = document.body?.innerText?.toLowerCase() || "";
  let role_type = null;
  if (bodyText.includes("full-time") || bodyText.includes("full time")) role_type = "full-time";
  else if (bodyText.includes("part-time") || bodyText.includes("part time")) role_type = "part-time";
  else if (bodyText.includes("contract")) role_type = "contract";
  else if (bodyText.includes("internship") || bodyText.includes("intern")) role_type = "internship";

  // Job description — try structured elements first
  const description =
    document.querySelector('[class*="description"], [class*="job-desc"], #job-description')
      ?.innerText?.trim() ||
    null;

  return { source_url, html, title, company_name, location, role_type, description };
}
