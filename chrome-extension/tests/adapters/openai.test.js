/**
 * @jest-environment-options {"url": "https://openai.com/careers/engineer-applied/"}
 */
"use strict";

const { openaiAdapter, slugToLocation, runAdapter } = require("../../content.js");

function makeDoc(html) {
  document.body.innerHTML = html;
  return document;
}

describe("openaiAdapter — company_name", () => {
  test("always returns OpenAI regardless of DOM", () => {
    makeDoc('<p>nothing</p>');
    expect(runAdapter(openaiAdapter, document).company_name).toBe("OpenAI");
  });
});

describe("slugToLocation", () => {
  test("san-francisco slug → San Francisco", () => {
    expect(slugToLocation("/careers/engineer-san-francisco/")).toBe("San Francisco");
  });

  test("new-york slug → New York", () => {
    expect(slugToLocation("/careers/engineer-new-york/")).toBe("New York");
  });

  test("remote slug → Remote", () => {
    expect(slugToLocation("/careers/engineer-remote/")).toBe("Remote");
  });

  test("unknown city in slug → null", () => {
    expect(slugToLocation("/careers/engineer-applied-foundations/")).toBeNull();
  });

  test("trailing slash handled", () => {
    expect(slugToLocation("/careers/engineer-london/")).toBe("London");
  });
});

describe("openaiAdapter — location", () => {
  test("reads <p> immediately after h2 inside main", () => {
    makeDoc('<main><h2>Engineer</h2><p>San Francisco, CA</p></main>');
    const result = runAdapter(openaiAdapter, document);
    expect(result.location).toBe("San Francisco, CA");
  });

  test("returns null when no p near h1 (falls back to generic via merge)", () => {
    makeDoc('<h1>Engineer</h1><div>other content</div>');
    // window.location.pathname (set via docblock above) is an unknown-city slug
    const result = runAdapter(openaiAdapter, document);
    expect(result.location).toBeNull();
  });
});

describe("openaiAdapter — description", () => {
  test("reads article element inside main", () => {
    makeDoc('<main><h2>Job</h2><article>This is the job description.</article></main>');
    expect(runAdapter(openaiAdapter, document).description).toBe("This is the job description.");
  });

  test("returns null when no article or main section", () => {
    makeDoc('<h1>Job</h1><p>short</p>');
    expect(runAdapter(openaiAdapter, document).description).toBeNull();
  });
});
