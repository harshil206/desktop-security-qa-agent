/**
 * Typed Preload API bridge exposed to the renderer context.
 */

export interface AppMetadata {
  name: string;
  version: string;
}

export interface ScannerHealthStatus {
  status: string;
  service: string;
}

export interface DesktopPreloadAPI {
  getAppMetadata: () => Promise<AppMetadata>;
  getHealth: () => Promise<ScannerHealthStatus>;
}
