"use strict";

const { genericAdapter, runAdapter } = require("../../content.js");

function makeDoc(html) {
  document.body.innerHTML = html;
  return document;
}

describe("genericAdapter — title", () => {
  test("extracts h1 text", () => {
    makeDoc('<h1>Senior Engineer</h1>');
    expect(runAdapter(genericAdapter, document).title).toBe("Senior Engineer");
  });

  test("falls back to document.title stripped of site name", () => {
    makeDoc('<p>no h1 here</p>');
    Object.defineProperty(document, "title", { value: "Senior Engineer | Acme", writable: true, configurable: true });
    expect(runAdapter(genericAdapter, document).title).toBe("Senior Engineer");
  });
});

describe("genericAdapter — company_name", () => {
  test("reads data-company attribute element", () => {
    makeDoc('<span data-company>Acme Corp</span>');
    expect(runAdapter(genericAdapter, document).company_name).toBe("Acme Corp");
  });

  test("reads og:site_name meta tag", () => {
    makeDoc('<meta property="og:site_name" content="Globex">');
    expect(runAdapter(genericAdapter, document).company_name).toBe("Globex");
  });

  test("returns empty string when nothing found", () => {
    makeDoc('<p>nothing here</p>');
    expect(runAdapter(genericAdapter, document).company_name).toBe("");
  });
});

describe("genericAdapter — location", () => {
  test("reads data-location element", () => {
    makeDoc('<span data-location>London, UK</span>');
    expect(runAdapter(genericAdapter, document).location).toBe("London, UK");
  });

  test("returns null when not found", () => {
    makeDoc('<p>no location</p>');
    expect(runAdapter(genericAdapter, document).location).toBeNull();
  });
});

describe("genericAdapter — role_type", () => {
  test("detects full-time from body text", () => {
    makeDoc('<p>This is a full-time position.</p>');
    expect(runAdapter(genericAdapter, document).role_type).toBe("full-time");
  });

  test("detects contract from body text", () => {
    makeDoc('<p>We need a contract developer.</p>');
    expect(runAdapter(genericAdapter, document).role_type).toBe("contract");
  });

  test("returns null when no role type found", () => {
    makeDoc('<p>come work with us</p>');
    expect(runAdapter(genericAdapter, document).role_type).toBeNull();
  });
});
