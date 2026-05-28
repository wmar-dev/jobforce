/**
 * Content script — runs in every page context.
 * Listens for CAPTURE_JOB messages from the background service worker,
 * extracts structured job data via the site adapter registry, and replies.
 *
 * To add a new site: add one entry to ADAPTERS keyed by hostname.
 * Each adapter declares only the fields it can extract; missing fields
 * fall back to the generic extractor automatically.
 */

/* ─── Generic adapter (works on most job boards) ─────────────────────────── */

function text(el) {
  return el ? (el.innerText ?? el.textContent ?? "").trim() : null;
}

const genericAdapter = {
  title: (doc) =>
    text(doc.querySelector("h1")) ||
    doc.title?.replace(/\s*[-|].*$/, "").trim() ||
    "",
  company_name: (doc) =>
    text(doc.querySelector("[data-company], .company-name, .employer-name")) ||
    doc.querySelector('meta[property="og:site_name"]')?.content ||
    "",
  location: (doc) =>
    text(doc.querySelector("[data-location], .job-location, .location")) ||
    doc.querySelector('meta[name="job:location"]')?.content ||
    null,
  description: (doc) =>
    text(doc.querySelector('[class*="description"], [class*="job-desc"], #job-description')) || null,
  role_type: (doc) => {
    const t = (doc.body?.innerText ?? doc.body?.textContent ?? "").toLowerCase();
    if (t.includes("full-time") || t.includes("full time")) return "full-time";
    if (t.includes("part-time") || t.includes("part time")) return "part-time";
    if (t.includes("contract")) return "contract";
    if (t.includes("internship") || t.includes("intern")) return "internship";
    return null;
  },
};

/* ─── Site-specific adapters ──────────────────────────────────────────────── */

/**
 * Parse a known city name from the trailing segment of a URL pathname.
 * e.g. "/careers/engineer-san-francisco/" → "San Francisco"
 */
function slugToLocation(pathname) {
  const seg = pathname.replace(/\/$/, "").split("/").pop() || "";
  const cities = ["san-francisco", "new-york", "london", "seattle", "remote", "boston", "chicago", "austin"];
  const hit = cities.find((c) => seg.endsWith(c));
  if (!hit) return null;
  return hit.split("-").map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");
}

const openaiAdapter = {
  company_name: () => "OpenAI",
  title: (doc) =>
    text(doc.querySelector("main h2")) || null,
  location: (doc) => {
    const domLoc = text(doc.querySelector("main h2 + p, main h2 ~ p"));
    return domLoc || slugToLocation(window.location.pathname) || null;
  },
  description: (doc) =>
    text(doc.querySelector("main article, main section")) || null,
  compensation: (doc) => {
    for (const el of doc.querySelectorAll("main p")) {
      const t = (el.innerText ?? el.textContent ?? "").trim();
      if (/^\$[\d,]/.test(t)) return t;
    }
    return null;
  },
};

const workdayAdapter = {
  // Workday: company name lives in the subdomain (tenant.wd1.myworkdayjobs.com)
  company_name: () => {
    const sub = window.location.hostname.split(".")[0];
    return sub ? sub[0].toUpperCase() + sub.slice(1) : null;
  },
  // Title is an h2 inside the job detail panel (h1 in banner is empty on Workday)
  title: (doc) => text(doc.querySelector('[data-automation-id="jobPostingHeader"] h2, .jobPostingTitle h2')) ||
    text(doc.querySelector("main h2, [role='main'] h2")) || null,
  // Location comes from the definition list: <dt>locations</dt><dd>...</dd>
  location: (doc) => {
    for (const dt of doc.querySelectorAll("dt, [data-automation-id='locations'] dd")) {
      if ((dt.innerText ?? dt.textContent ?? "").trim().toLowerCase() === "locations") {
        const dd = dt.nextElementSibling;
        return dd ? text(dd) : null;
      }
    }
    return null;
  },
  // role_type from the "time type" definition list entry
  role_type: (doc) => {
    for (const dt of doc.querySelectorAll("dt")) {
      if ((dt.innerText ?? dt.textContent ?? "").trim().toLowerCase() === "time type") {
        const dd = dt.nextElementSibling;
        const val = (dd ? (dd.innerText ?? dd.textContent ?? "") : "").toLowerCase();
        if (val.includes("full")) return "full-time";
        if (val.includes("part")) return "part-time";
        if (val.includes("contract")) return "contract";
        if (val.includes("intern")) return "internship";
      }
    }
    return null;
  },
  // Description: all paragraphs and list items in the main content section
  description: (doc) => {
    const section = doc.querySelector('[data-automation-id="jobPostingDescription"], .job-description, main section');
    if (section) return text(section) || null;
    // Fallback: gather paragraphs from the main content area
    const paras = doc.querySelectorAll("main p, [role='main'] p");
    const parts = Array.from(paras).map((p) => text(p)).filter(Boolean);
    return parts.length ? parts.join("\n\n") : null;
  },
  compensation: (doc) => {
    const all = doc.querySelectorAll("main p, [role='main'] p");
    for (const el of all) {
      const t = (el.innerText ?? el.textContent ?? "").trim();
      if (/\$[\d,]+/.test(t)) return t;
    }
    return null;
  },
};

const ashbyAdapter = {
  // Ashby pages have no <main> and no og:site_name; title tag is "<Role> @ <Company>"
  company_name: (doc) => {
    const m = doc.title?.match(/@\s*(.+)$/);
    return m ? m[1].trim() : null;
  },
  title: (doc) => text(doc.querySelector("h1")) || null,
  location: (doc) => {
    // Ashby renders labeled h2 + sibling p pairs
    for (const h2 of doc.querySelectorAll("h2")) {
      if ((h2.innerText ?? h2.textContent ?? "").trim() === "Location") {
        const p = h2.nextElementSibling;
        if (p && p.tagName === "P") return text(p) || null;
      }
    }
    return null;
  },
  compensation: (doc) => {
    for (const h2 of doc.querySelectorAll("h2")) {
      if ((h2.innerText ?? h2.textContent ?? "").trim() === "Compensation") {
        const list = h2.nextElementSibling;
        if (list) return text(list.querySelector("li") || list) || null;
      }
    }
    return null;
  },
  description: (doc) => text(doc.querySelector('[role="tabpanel"]')) || null,
};

/* ─── Registry: hostname → adapter ───────────────────────────────────────── */

const ADAPTERS = {
  "openai.com": openaiAdapter,
  "jobs.ashbyhq.com": ashbyAdapter,
  "myworkdayjobs.com": workdayAdapter,
  // "greenhouse.io": greenhouseAdapter,  // add future adapters here
  // "lever.co": leverAdapter,
  // "linkedin.com": linkedinAdapter,
};

/* ─── Framework: run adapter + merge ─────────────────────────────────────── */

/**
 * Call each field function on the adapter, catching errors individually.
 * Returns a partial JobFields object (only defined fields).
 */
function runAdapter(adapter, doc) {
  const result = {};
  for (const [key, fn] of Object.entries(adapter)) {
    try {
      result[key] = fn(doc);
    } catch (err) {
      console.warn(`[jobforce] adapter field ${key} error:`, err);
      result[key] = null;
    }
  }
  return result;
}

/**
 * Merge override into base — override fields win when non-null and non-empty.
 */
function merge(base, override) {
  const out = { ...base };
  for (const [k, v] of Object.entries(override)) {
    if (v != null && v !== "") out[k] = v;
  }
  return out;
}

function extractJobData() {
  const hostname = window.location.hostname.replace(/^www\./, "");
  // Exact match first, then suffix match (e.g. "myworkdayjobs.com" matches "tenant.wd1.myworkdayjobs.com")
  const adapter = ADAPTERS[hostname] ||
    Object.entries(ADAPTERS).find(([k]) => hostname.endsWith("." + k))?.[1];
  const base = runAdapter(genericAdapter, document);
  const override = adapter ? runAdapter(adapter, document) : {};
  return {
    source_url: window.location.href,
    html: document.documentElement.outerHTML,
    ...merge(base, override),
  };
}

/* ─── Message listener (Chrome extension runtime) ────────────────────────── */

if (typeof chrome !== "undefined" && chrome.runtime?.onMessage) {
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type !== "CAPTURE_JOB") return;
    try {
      const data = extractJobData();
      sendResponse({ ok: true, data });
    } catch (err) {
      sendResponse({ ok: false, error: String(err) });
    }
    return true;
  });
}

/* ─── Exports for Jest tests (no-op in browser context) ──────────────────── */

if (typeof module !== "undefined") {
  module.exports = { extractJobData, genericAdapter, openaiAdapter, ashbyAdapter, workdayAdapter, slugToLocation, runAdapter, merge };
}
