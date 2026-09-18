/**
 * @jest-environment-options {"url": "https://jobs.example.com/posting/123"}
 */
"use strict";

const { extractJobData } = require("../content.js");

function setDoc(html) {
  document.body.innerHTML = html;
}

describe("extractJobData — generic DOM (regression guard)", () => {
  test("title extracted from h1", () => {
    setDoc('<h1>Backend Developer</h1><span data-company>Acme</span>');
    expect(extractJobData().title).toBe("Backend Developer");
  });

  test("company_name extracted from data-company", () => {
    setDoc('<h1>Dev</h1><span data-company>Acme Corp</span>');
    expect(extractJobData().company_name).toBe("Acme Corp");
  });

  test("missing company returns empty string not undefined", () => {
    setDoc('<h1>Dev</h1>');
    const result = extractJobData();
    expect(result.company_name).toBe("");
    expect(result.company_name).not.toBeUndefined();
  });
});
