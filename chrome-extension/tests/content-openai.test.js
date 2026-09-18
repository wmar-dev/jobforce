/**
 * @jest-environment-options {"url": "https://openai.com/careers/full-stack-software-engineer-applied-foundations-san-francisco/"}
 */
"use strict";

const { extractJobData } = require("../content.js");

function setDoc(html) {
  document.body.innerHTML = html;
}

describe("extractJobData — OpenAI DOM", () => {
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

  test("location comes from p near h2 inside main", () => {
    setDoc('<main><h2>Engineer</h2><p>San Francisco, CA</p></main>');
    const result = extractJobData();
    expect(result.location).toBe("San Francisco, CA");
  });

  test("source_url is set", () => {
    setDoc('<h1>Engineer</h1>');
    const result = extractJobData();
    expect(result.source_url).toContain("openai.com");
  });
});
