# Penetration Test Report

## Executive Summary

Part B was executed against the authorized local target bundled with this workspace: the deployed `ledger-api` service in the `payments` namespace, reached through local port-forwarding at `http://127.0.0.1:18080`.

The service is still materially vulnerable. Two issues were verified directly:

- `GET /transactions` exposes full PAN values in the response body.
- `GET /fetch` behaves like an unrestricted outbound fetch primitive and will retrieve arbitrary remote URLs.

Both findings are high-signal in a PCI-sensitive application because they expose card data and create a server-side request primitive that can be chained into internal-network access depending on reachable destinations.

## Technical Summary

- Target: local `ledger-api` deployment in `payments`.
- Access method: `kubectl port-forward svc/ledger-api 18080:8080`.
- Active testing: manual HTTP requests against the local target.
- Scanner tooling: `nuclei`, `ffuf`, `sqlmap`, `zaproxy`, and `burpsuite` were not installed in this workspace, so verification was manual.
- Findings verified: 2.

## Rules of Engagement

- Only the authorized local target was tested.
- No production Dodo Payments property outside that target was probed.
- No stress testing, no DoS, no social engineering.
- Only verified issues are reported below.

## Methodology

1. Open a local port-forward to the deployed `ledger-api` service.
2. Verify baseline responses.
3. Probe high-risk endpoints manually.
4. Capture response bodies and headers as evidence.
5. Keep only findings that are directly reproduced.

## Findings

### 1. Full PAN Exposure in `/transactions`

- Severity: High
- CVSS v3.1: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` = 7.5
- Affected endpoint: `GET /transactions`
- Evidence: the response body includes complete PAN values such as `4242424242424242` and `5555555555554444`.
- Reproduction:
  ```bash
  curl -sS http://127.0.0.1:18080/transactions
  ```
- Impact: a remote unauthenticated caller can retrieve card-number data directly from the API response. In a PCI-scoped service, this is a material data exposure issue.
- Remediation: remove full PAN storage from the response path, store only tokens or masked suffixes, and enforce response filtering at the application boundary.
- Verification: rerun the endpoint after remediation and confirm only masked values or tokens are returned.

### 2. Unrestricted Outbound Fetch Primitive in `/fetch`

- Severity: High
- CVSS v3.1: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:L` = 8.6
- Affected endpoint: `GET /fetch?url=`
- Evidence: the endpoint successfully retrieves arbitrary external content from `http://example.com` and returns the remote body to the caller.
- Reproduction:
  ```bash
  curl -sS -i 'http://127.0.0.1:18080/fetch?url=http://example.com'
  ```
- Additional probe:
  ```bash
  curl -sS -i 'http://127.0.0.1:18080/fetch?url=http://127.0.0.1:8080/health'
  ```
  The localhost probe returned `500`, which still confirms the service attempts outbound retrieval and needs stricter allowlisting/validation.
- Impact: an attacker can force the service to make outbound requests on their behalf. In a real deployment this can be used for internal discovery, metadata access, or pivoting into sensitive network paths if any are reachable.
- Remediation: remove arbitrary URL fetching, or enforce a strict allowlist of approved hosts and schemes, with DNS/IP pinning and robust error handling.
- Verification: confirm non-approved URLs are rejected with a deterministic client error and no outbound request is made.

## Evidence Summary

- `GET /transactions` returned full PAN values.
- `GET /fetch?url=http://example.com` returned the external HTML body with HTTP 200.
- `GET /fetch?url=http://127.0.0.1:8080/health` returned HTTP 500.

## Retest

Retest is pending remediation of the target application.

## PDF-Ready Structure

### 1. Executive Summary

- Engagement context.
- High-level risk statement.
- Scope and exclusions.
- Top findings summary.

### 2. Scope and Rules of Engagement

- Authorized target.
- In-scope host and local port-forward.
- Out-of-scope production hosts.
- Rate limit and safety constraints.

### 3. Methodology

- Manual testing.
- Evidence capture.
- Retest process.

### 4. Findings

For each finding, include:

- Title
- Severity
- CVSS v3.1 vector and score
- Affected endpoint
- Reproduction steps
- Evidence
- Impact
- Remediation
- Verification

### 5. Retest

- Status after remediation.
- Evidence that the issue is closed.

### 6. Appendix

- Source links.
- Notes.
- Screenshots.

## Sources

- https://status.dodopayments.com/
- https://docs.dodopayments.com/
- https://docs.dodopayments.com/developer-resources/sdks/cli
- https://www.scamadviser.com/check-website/dodopayments.com
