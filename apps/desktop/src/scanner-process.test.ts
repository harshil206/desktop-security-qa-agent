import { describe, expect, it, vi } from "vitest";
import { ScannerProcessManager } from "./scanner-process";

describe("ScannerProcessManager Lifecycle", () => {
  it("initializes in STOPPED state with valid loopback host", () => {
    const manager = new ScannerProcessManager("127.0.0.1", 8000);
    expect(manager.getState()).toBe("STOPPED");
    expect(manager.getStatus().host).toBe("127.0.0.1");
  });

  it("rejects non-loopback host initialization", () => {
    expect(() => new ScannerProcessManager("0.0.0.0", 8000)).toThrow(/Security Violation/);
    expect(() => new ScannerProcessManager("192.168.1.5", 8000)).toThrow(/Security Violation/);
  });

  it("transitions to STARTING when markStarting is called", () => {
    const manager = new ScannerProcessManager();
    manager.markStarting(12345);
    expect(manager.getState()).toBe("STARTING");
    expect(manager.getStatus().pid).toBe(12345);
  });

  it("transitions to READY on successful health handshake", async () => {
    const manager = new ScannerProcessManager();
    manager.markStarting(12345);

    const mockFetch = vi.fn().mockResolvedValue({
      status: 200,
      json: async () => ({ status: "ok", service: "scanner" })
    });

    const success = await manager.performHandshake(mockFetch, 3, 10);
    expect(success).toBe(true);
    expect(manager.getState()).toBe("READY");
  });

  it("transitions to CRASHED when health handshake fails all attempts", async () => {
    const manager = new ScannerProcessManager();
    manager.markStarting(12345);

    const mockFetch = vi.fn().mockRejectedValue(new Error("Connection refused"));

    const success = await manager.performHandshake(mockFetch, 2, 10);
    expect(success).toBe(false);
    expect(manager.getState()).toBe("CRASHED");
  });

  it("handles unexpected exit by marking CRASHED", () => {
    const manager = new ScannerProcessManager();
    manager.markStarting(12345);
    manager.handleProcessExit(1, "SIGKILL");
    expect(manager.getState()).toBe("CRASHED");
    expect(manager.getStatus().lastExitCode).toBe(1);
  });

  it("handles clean termination by marking STOPPED", () => {
    const manager = new ScannerProcessManager();
    manager.markStarting(12345);
    manager.stopProcess();
    expect(manager.getState()).toBe("STOPPED");
  });
});
