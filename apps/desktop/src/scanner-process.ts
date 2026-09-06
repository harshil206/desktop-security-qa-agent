/**
 * Desktop-to-Scanner Process Ownership Manager.
 */

export type ScannerState = "STOPPED" | "STARTING" | "HANDSHAKE" | "READY" | "CRASHED" | "STOPPING";

export interface ScannerProcessStatus {
  state: ScannerState;
  host: string;
  port: number;
  pid: number | null;
  lastExitCode: number | null;
  logs: string[];
}

export class ScannerProcessManager {
  private state: ScannerState = "STOPPED";
  private host: string = "127.0.0.1";
  private port: number = 8000;
  private pid: number | null = null;
  private lastExitCode: number | null = null;
  private logs: string[] = [];

  constructor(host: string = "127.0.0.1", port: number = 8000) {
    if (host !== "127.0.0.1" && host !== "localhost" && host !== "::1") {
      throw new Error(`Security Violation: Scanner process host must be loopback (127.0.0.1 or localhost), received "${host}"`);
    }
    this.host = host;
    this.port = port;
  }

  public getStatus(): ScannerProcessStatus {
    return {
      state: this.state,
      host: this.host,
      port: this.port,
      pid: this.pid,
      lastExitCode: this.lastExitCode,
      logs: [...this.logs],
    };
  }

  public getState(): ScannerState {
    return this.state;
  }

  public log(message: string): void {
    this.logs.push(`[${new Date().toISOString()}] ${message}`);
  }

  public markStarting(pid: number): void {
    this.state = "STARTING";
    this.pid = pid;
    this.log(`Spawning scanner process with PID: ${pid} on ${this.host}:${this.port}`);
  }

  public async performHandshake(
    fetchFn: (url: string) => Promise<{ status: number; json: () => Promise<any> }>,
    maxRetries: number = 5,
    retryDelayMs: number = 50
  ): Promise<boolean> {
    this.state = "HANDSHAKE";
    this.log(`Initiating health handshake with scanner service at http://${this.host}:${this.port}/health`);

    const healthUrl = `http://${this.host}:${this.port}/health`;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetchFn(healthUrl);
        if (response.status === 200) {
          const body = await response.json();
          if (body && body.status === "ok" && body.service === "scanner") {
            this.state = "READY";
            this.log(`Health handshake succeeded on attempt ${attempt}. Scanner is READY.`);
            return true;
          }
        }
      } catch (err: any) {
        this.log(`Handshake attempt ${attempt} failed: ${err.message || err}`);
      }

      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, retryDelayMs));
      }
    }

    this.state = "CRASHED";
    this.log(`Health handshake failed after ${maxRetries} attempts. Transitioned to CRASHED.`);
    return false;
  }

  public handleProcessExit(exitCode: number | null, signal?: string): void {
    this.lastExitCode = exitCode;
    if (this.state !== "STOPPING") {
      this.state = "CRASHED";
      this.log(`Scanner process exited unexpectedly with code ${exitCode}, signal ${signal}. State: CRASHED.`);
    } else {
      this.state = "STOPPED";
      this.log(`Scanner process stopped cleanly with code ${exitCode}.`);
    }
    this.pid = null;
  }

  public stopProcess(): void {
    if (this.state === "STOPPED") {
      return;
    }
    this.state = "STOPPING";
    this.log(`Initiating clean shutdown of scanner process PID: ${this.pid}`);
    this.state = "STOPPED";
    this.pid = null;
  }
}
