/**
 * Manual test script for content.js DOM extraction.
 * Run in browser console on a job listing page to validate extraction.
 *
 * Usage: paste this into browser devtools console on any job board page.
 */

(function testContentExtraction() {
  "use strict";

  function extractJobData() {
    const source_url = window.location.href;
    const title =
      document.querySelector("h1")?.innerText?.trim() ||
      document.title?.replace(/\s*[-|].*$/, "").trim() ||
      "";
    const company_name =
      document.querySelector("[data-company], .company-name, .employer-name")
        ?.innerText?.trim() || "";
    const location =
      document.querySelector("[data-location], .job-location, .location")
        ?.innerText?.trim() || null;
    const description =
      document.querySelector(
        '[class*="description"], [class*="job-desc"], #job-description'
      )?.innerText?.trim() || null;
    return { source_url, title, company_name, location, description };
  }

  const result = extractJobData();
  const checks = [
    { field: "source_url", pass: result.source_url.startsWith("http") },
    { field: "title", pass: result.title.length > 0 },
    { field: "company_name", pass: true }, // optional — may be empty on some boards
    { field: "location", pass: true }, // optional
    { field: "description", pass: true }, // optional
  ];

  console.group("Jobforce Scout — Content Extraction Test");
  checks.forEach(({ field, pass }) => {
    console.log(`${pass ? "✅" : "❌"} ${field}: ${JSON.stringify(result[field])}`);
  });
  const allRequired = checks
    .filter((c) => ["source_url", "title"].includes(c.field))
    .every((c) => c.pass);
  console.log(allRequired ? "✅ PASS — required fields extracted" : "❌ FAIL — missing required fields");
  console.groupEnd();

  return result;
})();
