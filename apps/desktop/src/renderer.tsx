/**
 * React Root Renderer Component.
 */
import React from "react";
import { ScanSetupForm } from "./ScanSetupForm";

export function AppShell() {
  return (
    <div className="app-container">
      <ScanSetupForm />
    </div>
  );
}

export function getRendererConfig() {
  return {
    title: "Desktop Website Security & QA Agent",
    sandboxed: true,
    nodeIntegration: false,
    contextIsolation: true
  };
}
