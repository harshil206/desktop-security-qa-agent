/**
 * React Root Renderer Component.
 */
export function AppShell() {
  return {
    title: "Desktop Website Security & QA Agent",
    sandboxed: true,
    nodeIntegration: false,
    contextIsolation: true
  };
}
