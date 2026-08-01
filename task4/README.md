# Task 4 - Reconnaissance and Penetration Testing

## Scope

This task is split into two parts:

- Part A: passive reconnaissance of `dodopayments.tech` using public sources only.
- Part B: active testing only against an explicitly authorized target. No target is bundled in this workspace, so Part B is documented as pending until the authorized target is provided.

## Rules of Engagement

- Passive recon only for `dodopayments.tech` and related public properties.
- No DoS, no stress testing, no social engineering.
- No active probing of production Dodo Payments hosts unless a target is explicitly authorized for this task.
- Do not fabricate findings. Only report verified observations.

## What is included

- `task4/attack-surface-report.md`: passive attack surface inventory for public Dodo Payments properties.
- `task4/penetration-test-report.md`: PDF-ready report structure for the authorized target, with the current status noted as pending because no authorized target is bundled here.

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
- Part B: pending an explicitly authorized target.
- No commits were made.


## Screenshots To Capture

- Status page showing the public service breakdown.
- Documentation page showing the public dashboard link.
- Third-party summary showing the `.tech` redirect family.
- Final report file tree for submission.

## Next Verification Checklist

- Confirm the report links render from the top-level README.
- Confirm the attack-surface report only contains verified public observations.
- Confirm the penetration-test report states that Part B is pending an authorized target.
- Confirm no fabricated findings are present.
