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
  test("reads <p> immediately after h1", () => {
    makeDoc('<h1>Engineer</h1><p>San Francisco, CA</p>');
    const result = runAdapter(openaiAdapter, document);
    expect(result.location).toBe("San Francisco, CA");
  });

  test("returns null when no p near h1 (falls back to generic via merge)", () => {
    makeDoc('<h1>Engineer</h1><div>other content</div>');
    // Override window.location.pathname to unknown city
    Object.defineProperty(window, "location", {
      value: { ...window.location, pathname: "/careers/engineer-applied/" },
      writable: true,
      configurable: true,
    });
    const result = runAdapter(openaiAdapter, document);
    expect(result.location).toBeNull();
  });
});

describe("openaiAdapter — description", () => {
  test("reads article element", () => {
    makeDoc('<h1>Job</h1><article>This is the job description.</article>');
    expect(runAdapter(openaiAdapter, document).description).toBe("This is the job description.");
  });

  test("returns null when no article or main section", () => {
    makeDoc('<h1>Job</h1><p>short</p>');
    expect(runAdapter(openaiAdapter, document).description).toBeNull();
  });
});
