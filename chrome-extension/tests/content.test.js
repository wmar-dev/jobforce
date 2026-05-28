"use strict";

const { extractJobData } = require("../content.js");

function setDoc(html) {
  document.body.innerHTML = html;
}

describe("extractJobData — OpenAI DOM", () => {
  beforeEach(() => {
    Object.defineProperty(window, "location", {
      value: {
        href: "https://openai.com/careers/full-stack-software-engineer-applied-foundations-san-francisco/",
        hostname: "openai.com",
        pathname: "/careers/full-stack-software-engineer-applied-foundations-san-francisco/",
      },
      writable: true,
      configurable: true,
    });
  });

  test("company_name is OpenAI", () => {
    setDoc('<h1>Full Stack Software Engineer</h1><p>San Francisco, CA</p><article>Great job description here.</article>');
    const result = extractJobData();
    expect(result.company_name).toBe("OpenAI");
  });

  test("title comes from h1", () => {
    setDoc('<h1>Full Stack Software Engineer</h1><p>San Francisco, CA</p>');
    const result = extractJobData();
    expect(result.title).toBe("Full Stack Software Engineer");
  });

  test("location comes from p near h1", () => {
    setDoc('<h1>Engineer</h1><p>San Francisco, CA</p>');
    const result = extractJobData();
    expect(result.location).toBe("San Francisco, CA");
  });

  test("source_url is set", () => {
    setDoc('<h1>Engineer</h1>');
    const result = extractJobData();
    expect(result.source_url).toContain("openai.com");
  });
});

describe("extractJobData — generic DOM (regression guard)", () => {
  beforeEach(() => {
    Object.defineProperty(window, "location", {
      value: {
        href: "https://jobs.example.com/posting/123",
        hostname: "jobs.example.com",
        pathname: "/posting/123",
      },
      writable: true,
      configurable: true,
    });
  });

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
