import { describe, expect, it } from "vitest";
import { desktopAPI } from "./preload";

describe("Preload Cancellation and Emergency Stop API", () => {
  it("resolves cancelScan with cancelled status and reason", async () => {
    const res = await desktopAPI.cancelScan("SCAN-100", "User requested cancel");
    expect(res.status).toBe("cancelled");
    expect(res.reason).toBe("User requested cancel");
  });

  it("resolves emergencyStop with blocked status and reason", async () => {
    const res = await desktopAPI.emergencyStop("SCAN-100", "Critical error observed");
    expect(res.status).toBe("blocked");
    expect(res.reason).toBe("Critical error observed");
  });
});
