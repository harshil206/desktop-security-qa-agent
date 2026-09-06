import { describe, expect, it } from "vitest";
import { SECURE_WEB_PREFERENCES, validateWindowSecurity } from "./window-config";

describe("SECURE_WEB_PREFERENCES", () => {
  it("enforces nodeIntegration is false", () => {
    expect(SECURE_WEB_PREFERENCES.nodeIntegration).toBe(false);
  });

  it("enforces contextIsolation is true", () => {
    expect(SECURE_WEB_PREFERENCES.contextIsolation).toBe(true);
  });

  it("enforces sandbox is true", () => {
    expect(SECURE_WEB_PREFERENCES.sandbox).toBe(true);
  });

  it("enforces webSecurity is true", () => {
    expect(SECURE_WEB_PREFERENCES.webSecurity).toBe(true);
  });
});

describe("validateWindowSecurity", () => {
  it("passes for SECURE_WEB_PREFERENCES", () => {
    expect(validateWindowSecurity(SECURE_WEB_PREFERENCES)).toBe(true);
  });

  it("throws error if nodeIntegration is enabled", () => {
    const unsafe = { ...SECURE_WEB_PREFERENCES, nodeIntegration: true };
    expect(() => validateWindowSecurity(unsafe)).toThrow(/nodeIntegration must be strictly false/);
  });

  it("throws error if contextIsolation is disabled", () => {
    const unsafe = { ...SECURE_WEB_PREFERENCES, contextIsolation: false };
    expect(() => validateWindowSecurity(unsafe)).toThrow(/contextIsolation must be strictly true/);
  });

  it("throws error if sandbox is disabled", () => {
    const unsafe = { ...SECURE_WEB_PREFERENCES, sandbox: false };
    expect(() => validateWindowSecurity(unsafe)).toThrow(/sandbox must be strictly true/);
  });
});
