/**
 * Electron Main Process entry point.
 */
import { SECURE_WEB_PREFERENCES, validateWindowSecurity } from "./window-config";

export function createBrowserWindowOptions(preloadPath?: string) {
  const webPreferences = {
    ...SECURE_WEB_PREFERENCES,
    preload: preloadPath,
  };
  validateWindowSecurity(webPreferences);
  return {
    width: 1200,
    height: 800,
    title: "Desktop Website Security & QA Agent",
    webPreferences,
  };
}
