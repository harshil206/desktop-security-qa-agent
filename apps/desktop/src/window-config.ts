/**
 * Electron BrowserWindow security configuration options.
 */

export interface SecureWebPreferences {
  readonly nodeIntegration: boolean;
  readonly contextIsolation: boolean;
  readonly sandbox: boolean;
  readonly webSecurity: boolean;
  readonly allowRunningInsecureContent: boolean;
  readonly preload?: string;
}

export const SECURE_WEB_PREFERENCES: SecureWebPreferences = {
  nodeIntegration: false,
  contextIsolation: true,
  sandbox: true,
  webSecurity: true,
  allowRunningInsecureContent: false,
};

export function validateWindowSecurity(prefs: SecureWebPreferences): boolean {
  if (prefs.nodeIntegration !== false) {
    throw new Error("Security Violation: nodeIntegration must be strictly false.");
  }
  if (prefs.contextIsolation !== true) {
    throw new Error("Security Violation: contextIsolation must be strictly true.");
  }
  if (prefs.sandbox !== true) {
    throw new Error("Security Violation: sandbox must be strictly true.");
  }
  if (prefs.webSecurity !== true) {
    throw new Error("Security Violation: webSecurity must be strictly true.");
  }
  return true;
}
