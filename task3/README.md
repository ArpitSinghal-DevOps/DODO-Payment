# Task 3 - Application Security Remediation

## Objective

Remediate the application-level risks intentionally left visible after Tasks 1 and 2 so the container pipeline can pass strict vulnerability and security review gates.

## Changes

- Replaced unsafe `yaml.load` with `yaml.safe_load`.
- Upgraded the Python runtime and package pins in `app/`.
- Removed full PAN values from the transaction response and retained only `pan_last4`.
- Added SSRF protection to `/fetch`:
  - only `http` and `https` URLs are accepted;
  - hostnames must resolve successfully;
  - every resolved address must be globally routable;
  - loopback, private, link-local, multicast, unspecified, and reserved addresses are rejected;
  - automatic redirects are disabled to avoid redirecting from a public URL to an internal target.
- Added focused regression tests for PAN redaction and `/fetch` URL validation.

## Verification

Run local tests:

```bash
python3 -m unittest discover -s tests
```

Compile the app:

```bash
python3 -m compileall app
```

Build the container:

```bash
docker build -t ledger-api:task3 ./app
```

## Remaining Production Considerations

`/fetch` is now guarded against common SSRF paths. For production, prefer removing generic remote fetch capability entirely or replacing it with an explicit allowlist of partner hostnames.
