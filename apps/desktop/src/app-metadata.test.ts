import { describe, expect, it } from "vitest";

import { APP_NAME, APP_VERSION, formatAppTitle, getAppMetadata } from "./app-metadata";

describe("getAppMetadata", () => {
  it("returns the configured application name and version", () => {
    expect(getAppMetadata()).toEqual({ name: APP_NAME, version: APP_VERSION });
  });

  it("reports a semver-like version", () => {
    expect(APP_VERSION).toMatch(/^\d+\.\d+\.\d+$/);
  });
});

describe("formatAppTitle", () => {
  it("joins a valid name and version", () => {
    expect(formatAppTitle({ name: "Example App", version: "1.2.3" })).toBe("Example App 1.2.3");
  });

  it("trims surrounding whitespace", () => {
    const title = formatAppTitle({ name: "  Example App  ", version: " 1.2.3 " });
    expect(title).toBe("Example App 1.2.3");
  });

  it("rejects an empty name", () => {
    expect(() => formatAppTitle({ name: "   ", version: "1.0.0" })).toThrow(/must not be empty/);
  });

  it("rejects a version that is not semver-like", () => {
    expect(() => formatAppTitle({ name: "Example App", version: "beta" })).toThrow(/semver-like/);
  });
});
