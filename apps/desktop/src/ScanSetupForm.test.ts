import { describe, expect, it } from "vitest";
import { desktopAPI } from "./preload";

describe("ScanSetupForm Preload API Bridge", () => {
  it("validates compliant policy payload via preload bridge", async () => {
    const payload = {
      authorization: {
        contact_email: "test@example.com",
        authorized_by: "Tester",
        owner_confirmed: true,
        target_domains: ["example.com"]
      },
      target_domains: ["example.com"],
      allowed_url_prefixes: ["https://example.com/"],
      max_depth: 3,
      requests_per_minute: 60,
      total_request_budget: 500,
      max_duration_seconds: 1800,
      scan_mode: "passive"
    };

    const res = await desktopAPI.validatePolicy(payload);
    expect(res.valid).toBe(true);
  });

  it("rejects policy payload without owner_confirmed", async () => {
    const payload = {
      authorization: {
        owner_confirmed: false
      },
      target_domains: ["example.com"],
      allowed_url_prefixes: ["https://example.com/"]
    };

    const res = await desktopAPI.validatePolicy(payload);
    expect(res.valid).toBe(false);
    expect(res.errors).toContain("Owner authorization confirmation is required.");
  });

  it("rejects policy payload without target_domains", async () => {
    const payload = {
      authorization: {
        owner_confirmed: true
      },
      target_domains: [],
      allowed_url_prefixes: ["https://example.com/"]
    };

    const res = await desktopAPI.validatePolicy(payload);
    expect(res.valid).toBe(false);
    expect(res.errors).toContain("At least one target domain is required.");
  });
});
