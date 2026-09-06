import { describe, expect, it } from "vitest";
import { desktopAPI } from "./preload";

describe("desktopAPI Preload Bridge", () => {
  it("resolves getAppMetadata correctly", async () => {
    const meta = await desktopAPI.getAppMetadata();
    expect(meta).toEqual({
      name: "Desktop Website Security & QA Agent",
      version: "0.1.0"
    });
  });

  it("resolves getHealth status", async () => {
    const health = await desktopAPI.getHealth();
    expect(health).toEqual({
      status: "ok",
      service: "scanner"
    });
  });
});
