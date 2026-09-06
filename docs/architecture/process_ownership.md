# Process Ownership and Lifecycle Specification

This document specifies how the Electron desktop main process manages, monitors, and terminates the local FastAPI scanner service process.

## 1. Process Hierarchy & Ownership Model

- **Parent Process:** Electron Main Process (`apps/desktop`).
- **Child Process:** FastAPI Scanner Service (`services/scanner`).
- **Binding Rule:** The scanner process binds strictly to loopback (`127.0.0.1:8000`). It is never exposed to external LAN interfaces.
- **Ownership:** The scanner service process is strictly owned by the Electron application instance. Closing the desktop app guarantees termination of the scanner process.

---

## 2. Process Lifecycle States

| State | Description |
| :--- | :--- |
| `STOPPED` | No scanner child process is running. |
| `STARTING` | Electron main process spawns the Python FastAPI subprocess. |
| `HANDSHAKE` | Electron main process polls `GET http://127.0.0.1:8000/health`. |
| `READY` | Health endpoint returns 200 OK with `{"status": "ok", "service": "scanner"}`. |
| `CRASHED` | Child process exited unexpectedly or failed health handshake timeout budget. |
| `STOPPING` | Electron main process is terminating the child process. |

---

## 3. Health Handshake Protocol

1. **Initiation:** Upon spawning the child process, Electron enters `HANDSHAKE` state.
2. **Polling:** Electron issues HTTP GET requests to `http://127.0.0.1:8000/health`.
3. **Retry Budget:** Polling occurs up to 10 attempts at 500ms intervals (5.0s max timeout).
4. **Validation:** State transitions to `READY` when `response.status === 200` and `response.json.status === "ok"`.
5. **Timeout Handling:** If all retry attempts fail, the scanner manager marks the state as `CRASHED` and logs an error.

---

## 4. Termination & Emergency Stop Procedure

When the Electron application is exiting or a restart is requested:

1. **State Transition:** State transitions to `STOPPING`.
2. **Graceful Signal (SIGTERM):** Send `SIGTERM` signal to the child process.
3. **Grace Period:** Wait up to 2.0 seconds for clean exit.
4. **Forced Termination (SIGKILL):** If the process has not exited after 2.0s, issue `SIGKILL` to force exit.
5. **Post-Condition:** State transitions to `STOPPED`.
