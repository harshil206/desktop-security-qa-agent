import React, { useState } from "react";
import { desktopAPI } from "./preload";

export function ScanSetupForm() {
  const [contactEmail, setContactEmail] = useState("security@example.com");
  const [authorizedBy, setAuthorizedBy] = useState("Jane Doe");
  const [ownerConfirmed, setOwnerConfirmed] = useState(false);
  const [targetDomains, setTargetDomains] = useState("example.com");
  const [allowedUrlPrefixes, setAllowedUrlPrefixes] = useState("https://example.com/");
  const [maxDepth, setMaxDepth] = useState(3);
  const [requestsPerMinute, setRequestsPerMinute] = useState(60);
  const [totalRequestBudget, setTotalRequestBudget] = useState(500);
  const [maxDurationSeconds, setMaxDurationSeconds] = useState(1800);

  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isValidated, setIsValidated] = useState(false);

  const handleValidate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setValidationErrors([]);
    setIsValidated(false);

    const now = new Date();
    const validUntil = new Date(now.getTime() + 2 * 60 * 60 * 1000);

    const payload = {
      authorization: {
        contact_email: contactEmail.trim(),
        authorized_by: authorizedBy.trim(),
        owner_confirmed: ownerConfirmed,
        valid_from: now.toISOString(),
        valid_until: validUntil.toISOString(),
        target_domains: targetDomains.split(",").map((d) => d.trim()).filter(Boolean),
      },
      target_domains: targetDomains.split(",").map((d) => d.trim()).filter(Boolean),
      allowed_url_prefixes: allowedUrlPrefixes.split(",").map((p) => p.trim()).filter(Boolean),
      max_depth: maxDepth,
      requests_per_minute: requestsPerMinute,
      total_request_budget: totalRequestBudget,
      max_duration_seconds: maxDurationSeconds,
      scan_mode: "passive",
      allowed_http_methods: ["GET", "HEAD"],
    };

    const api = (window as any).electronAPI || desktopAPI;
    const result = await api.validatePolicy(payload);

    if (result.valid) {
      setIsValidated(true);
    } else {
      setValidationErrors(result.errors || ["Scan policy validation failed."]);
    }
  };

  return (
    <div style={{ maxWidth: "680px", margin: "0 auto", padding: "1.5rem", color: "#f8fafc" }}>
      <h2>New Scan Setup</h2>
      <p style={{ color: "#94a3b8", fontSize: "0.9rem" }}>
        Configure target scope, rules of engagement, and scan budgets. Scanner is restricted to <strong>Passive (Read-Only)</strong> mode.
      </p>

      {isValidated && (
        <div style={{ backgroundColor: "#065f46", color: "#34d399", padding: "0.75rem", borderRadius: "6px", marginBottom: "1rem" }}>
          ✓ Scan Policy successfully validated! Ready to queue scan job.
        </div>
      )}

      {validationErrors.length > 0 && (
        <div style={{ backgroundColor: "#7f1d1d", color: "#fca5a5", padding: "0.75rem", borderRadius: "6px", marginBottom: "1rem" }}>
          <strong>Policy Validation Errors:</strong>
          <ul style={{ margin: "0.5rem 0 0 1rem", padding: 0 }}>
            {validationErrors.map((err, idx) => (
              <li key={idx}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={handleValidate}>
        <fieldset style={{ border: "1px solid #334155", borderRadius: "6px", padding: "1rem", marginBottom: "1rem" }}>
          <legend style={{ color: "#38bdf8", padding: "0 0.5rem", fontWeight: 600 }}>1. Target Ownership & Authorization</legend>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", marginBottom: "0.25rem" }}>Contact Email:</label>
            <input
              type="email"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", borderRadius: "4px", border: "1px solid #475569", background: "#0f172a", color: "#fff" }}
              required
            />
          </div>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", marginBottom: "0.25rem" }}>Authorized By:</label>
            <input
              type="text"
              value={authorizedBy}
              onChange={(e) => setAuthorizedBy(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", borderRadius: "4px", border: "1px solid #475569", background: "#0f172a", color: "#fff" }}
              required
            />
          </div>
          <div style={{ marginTop: "0.5rem" }}>
            <label style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "0.5rem", color: "#f1f5f9" }}>
              <input
                type="checkbox"
                checked={ownerConfirmed}
                onChange={(e) => setOwnerConfirmed(e.target.checked)}
                id="owner-confirmation-checkbox"
              />
              <strong>I confirm that I own this target or have explicit authorization to assess it.</strong>
            </label>
          </div>
        </fieldset>

        <fieldset style={{ border: "1px solid #334155", borderRadius: "6px", padding: "1rem", marginBottom: "1rem" }}>
          <legend style={{ color: "#38bdf8", padding: "0 0.5rem", fontWeight: 600 }}>2. Target Domain & Path Scope</legend>
          <div style={{ marginBottom: "0.75rem" }}>
            <label style={{ display: "block", marginBottom: "0.25rem" }}>Target Domain(s) (comma separated):</label>
            <input
              type="text"
              value={targetDomains}
              onChange={(e) => setTargetDomains(e.target.value)}
              placeholder="example.com"
              style={{ width: "100%", padding: "0.5rem", borderRadius: "4px", border: "1px solid #475569", background: "#0f172a", color: "#fff" }}
              required
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: "0.25rem" }}>Allowed URL Prefixes (comma separated):</label>
            <input
              type="text"
              value={allowedUrlPrefixes}
              onChange={(e) => setAllowedUrlPrefixes(e.target.value)}
              placeholder="https://example.com/"
              style={{ width: "100%", padding: "0.5rem", borderRadius: "4px", border: "1px solid #475569", background: "#0f172a", color: "#fff" }}
              required
            />
          </div>
        </fieldset>

        <fieldset style={{ border: "1px solid #334155", borderRadius: "6px", padding: "1rem", marginBottom: "1rem" }}>
          <legend style={{ color: "#38bdf8", padding: "0 0.5rem", fontWeight: 600 }}>3. Conservative Scan Budgets</legend>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div>
              <label>Crawl Depth (Max: 5): {maxDepth}</label>
              <input type="range" min="1" max="5" value={maxDepth} onChange={(e) => setMaxDepth(Number(e.target.value))} style={{ width: "100%" }} />
            </div>
            <div>
              <label>Requests / Min (Max: 120): {requestsPerMinute}</label>
              <input type="range" min="1" max="120" value={requestsPerMinute} onChange={(e) => setRequestsPerMinute(Number(e.target.value))} style={{ width: "100%" }} />
            </div>
            <div>
              <label>Request Budget (Max: 1000): {totalRequestBudget}</label>
              <input type="range" min="10" max="1000" step="10" value={totalRequestBudget} onChange={(e) => setTotalRequestBudget(Number(e.target.value))} style={{ width: "100%" }} />
            </div>
            <div>
              <label>Duration (Seconds, Max: 3600): {maxDurationSeconds}</label>
              <input type="range" min="60" max="3600" step="60" value={maxDurationSeconds} onChange={(e) => setMaxDurationSeconds(Number(e.target.value))} style={{ width: "100%" }} />
            </div>
          </div>
        </fieldset>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem" }}>
          <div>
            <span style={{ background: "#1e293b", border: "1px solid #334155", padding: "0.4rem 0.8rem", borderRadius: "4px", fontSize: "0.85rem" }}>
              Mode: <strong>PASSIVE (Read-Only)</strong>
            </span>
          </div>
          <button
            type="submit"
            style={{
              background: ownerConfirmed ? "#2563eb" : "#475569",
              color: "#fff",
              padding: "0.6rem 1.5rem",
              borderRadius: "6px",
              border: "none",
              fontWeight: 600,
              cursor: ownerConfirmed ? "pointer" : "not-allowed",
            }}
            disabled={!ownerConfirmed}
          >
            Validate & Save Policy
          </button>
        </div>
      </form>
    </div>
  );
}
