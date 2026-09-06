/**
 * Static desktop application metadata.
 *
 * Placeholder module created by task P1-01 so the TypeScript, lint, and unit
 * test gates have real code to verify. It performs no I/O and touches no
 * native capability. The Electron main process, preload bridge, and React
 * renderer are added by task P1-03.
 */

export const APP_NAME = "Desktop Website Security & QA Agent";
export const APP_VERSION = "0.1.0";

const SEMVER_PATTERN = /^\d+\.\d+\.\d+$/;

export interface AppMetadata {
  readonly name: string;
  readonly version: string;
}

export function getAppMetadata(): AppMetadata {
  return { name: APP_NAME, version: APP_VERSION };
}

export function formatAppTitle(metadata: AppMetadata): string {
  const name = metadata.name.trim();
  if (name.length === 0) {
    throw new Error("App metadata name must not be empty.");
  }

  const version = metadata.version.trim();
  if (!SEMVER_PATTERN.test(version)) {
    throw new Error(`App metadata version must be semver-like, received: "${version}"`);
  }

  return `${name} ${version}`;
}
