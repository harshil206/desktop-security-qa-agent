/**
 * Electron Preload script exposing typed contextBridge API.
 */
import { DesktopPreloadAPI, PolicyValidationResult, ScanControlResult } from "./preload-api";

export const desktopAPI: DesktopPreloadAPI = {
  getAppMetadata: async () => ({
    name: "Desktop Website Security & QA Agent",
    version: "0.1.0"
  }),
  getHealth: async () => ({
    status: "ok",
    service: "scanner"
  }),
  validatePolicy: async (policyPayload: any): Promise<PolicyValidationResult> => {
    if (!policyPayload?.authorization?.owner_confirmed) {
      return { valid: false, errors: ["Owner authorization confirmation is required."] };
    }
    if (!policyPayload?.target_domains || policyPayload.target_domains.length === 0) {
      return { valid: false, errors: ["At least one target domain is required."] };
    }
    if (!policyPayload?.allowed_url_prefixes || policyPayload.allowed_url_prefixes.length === 0) {
      return { valid: false, errors: ["At least one allowed URL prefix is required."] };
    }
    return { valid: true, policy: policyPayload };
  },
  cancelScan: async (scanId: string, reason?: string): Promise<ScanControlResult> => {
    return {
      status: "cancelled",
      reason: reason || "User initiated cancellation"
    };
  },
  emergencyStop: async (scanId: string, reason?: string): Promise<ScanControlResult> => {
    return {
      status: "blocked",
      reason: reason || "Emergency stop triggered"
    };
  }
};

// When running inside Electron main context:
if (typeof window !== "undefined") {
  try {
    const { contextBridge } = require("electron");
    contextBridge.exposeInMainWorld("electronAPI", desktopAPI);
  } catch {
    // Non-Electron execution context
  }
}
