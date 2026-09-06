/**
 * Electron Preload script exposing typed contextBridge API.
 */
import { DesktopPreloadAPI } from "./preload-api";

export const desktopAPI: DesktopPreloadAPI = {
  getAppMetadata: async () => ({
    name: "Desktop Website Security & QA Agent",
    version: "0.1.0"
  }),
  getHealth: async () => ({
    status: "ok",
    service: "scanner"
  })
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
