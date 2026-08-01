# Task 4 - Reconnaissance and Penetration Testing

## Scope

This task is split into two parts:

- Part A: passive reconnaissance of `dodopayments.tech` using public sources only.
- Part B: active testing against the authorized local target bundled with this workspace, the deployed `ledger-api` service in `payments`.

## Rules of Engagement

- Passive recon only for `dodopayments.tech` and related public properties.
- No DoS, no stress testing, no social engineering.
- Active testing is limited to the local `ledger-api` service in `payments`.
- Do not fabricate findings. Only report verified observations.

## What is included

- `task4/attack-surface-report.md`: passive attack surface inventory for public Dodo Payments properties.
- `task4/penetration-test-report.md`: report for the authorized local target with verified findings and evidence.

## Tools Covered

The assignment references the following tools and their roles:

- `crt.sh`: certificate transparency enumeration.
- `subfinder`, `assetfinder`, `amass`: passive subdomain discovery.
- `httpx`, `whatweb`: live host and technology fingerprinting.
- `testssl.sh`: TLS posture review.
- `Burp Suite Community`, `OWASP ZAP`: web application interception and manual/automated testing.
- `nuclei`: template-driven verification of known issues.
- `ffuf`: content and parameter discovery.
- `sqlmap`: SQL injection verification when a finding is already suspected and in scope.

## Source Set Used For Part A

- Dodo Payments status page: https://status.dodopayments.com/
- Dodo Payments documentation: https://docs.dodopayments.com/
- Dodo CLI docs page showing the public dashboard link: https://docs.dodopayments.com/developer-resources/sdks/cli
- Scamadviser third-party summary for the `.tech` domain family: https://www.scamadviser.com/check-website/dodopayments.com

## Current Status

- Part A: drafted from public sources.
- Part B: executed against the local `ledger-api` target with verified findings.
- No commits were made.

## Screenshots To Capture

- Status page showing the public service breakdown.
- Documentation page showing the public dashboard link.
- Local terminal showing the port-forward to `ledger-api`.
- `GET /transactions` response showing full PAN exposure.
- `GET /fetch?url=http://example.com` response body and headers.
- Final report file tree for submission.

## Next Verification Checklist

- Confirm the report links render from the top-level README.
- Confirm the attack-surface report only contains verified public observations.
- Confirm the penetration-test report includes only reproduced findings.
- Confirm no fabricated findings are present.
