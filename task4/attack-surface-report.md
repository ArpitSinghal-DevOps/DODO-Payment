# Attack Surface Report

## Executive Summary

Publicly visible Dodo Payments properties expose a fairly broad payment-platform surface: marketing, documentation, dashboard, checkout, customer portal, transactional APIs, email services, and webhook services. The public status page confirms these are first-class services, and the documentation exposes the dashboard application and developer tooling.

The main defensive observation is that the company has already segmented its public surface by function. The main residual risk is that payment, customer, and developer surfaces are all reachable over the public internet and therefore need strong auth, anti-automation controls, and careful secret handling.

## Verified Public Surface

| Surface | Evidence | Why it matters | Risk observation |
|---|---|---|---|
| Website | Status page lists `Website` under Frontend Services. | Internet-facing entry point for users and attackers alike. | Marketing sites often reveal product names, route patterns, and vendor fingerprints. |
| Dashboard | Status page lists `Dashboard`; docs link to `app.dodopayments.com`. | Primary operator interface. | High-value target for account takeover, session theft, and phishing. |
| Docs | Status page lists `Docs`; docs are publicly hosted on Mintlify. | Public developer documentation. | Docs can leak API shapes, auth flows, and operational dependencies. |
| Checkout | Status page lists `Checkout`. | Transaction entry point. | Likely sensitive to payment flow manipulation and abuse controls. |
| Customer Portal | Status page lists `Customer Portal`. | Customer self-service entry point. | Likely exposed to auth/session abuse and IDOR-style mistakes. |
| Live Mode Prod APIs | Status page lists `Live Mode Prod APIs`. | Production payment APIs. | Highest sensitivity surface; should be tightly controlled and monitored. |
| Test Mode Prod APIs | Status page lists `Test Mode Prod APIs`. | Non-production API path. | Test environments often leak weaker controls or extra debug paths. |
| Internal Prod APIs | Status page lists `Internal Prod APIs`. | Internal backend surface. | Needs strong network and identity boundaries to avoid lateral access. |
| Email Services | Status page lists `Email Services`. | Transactional mail path. | Can be abused for phishing or message spoofing if misconfigured. |
| Webhook Services | Status page lists `Webhook Services`. | Outbound integration surface. | Webhook signing, retry logic, and allowlists are common failure points. |

## Domain Posture

A third-party public summary reports that `dodopayments.tech` redirects into the main Dodo Payments web presence and that the site family is fronted by Cloudflare with Google Trust Services certificates. Treat that as supplemental intelligence, not a direct probe result.

Reference: https://www.scamadviser.com/check-website/dodopayments.com

## Recon Notes

The documentation portal is itself a useful attack surface map because it exposes product names and public service links. The docs navigation shows a dashboard link to `app.dodopayments.com`, and the status page shows the operational split between frontend and backend services.

Relevant sources:

- https://status.dodopayments.com/
- https://docs.dodopayments.com/
- https://docs.dodopayments.com/developer-resources/sdks/cli

## Risk Observations

- The dashboard and customer portal are likely the highest-value targets for account takeover and session abuse.
- Public docs can leak endpoint structure, auth expectations, and integration assumptions.
- Public webhook and email services need strong signature validation and anti-abuse controls.
- Production API segmentation is good, but the surface still needs strict monitoring and rate limiting.

## What I Would Verify Next With Authorization

Only if an explicit authorized target is provided for Part B:

- authentication and session handling on the dashboard or portal
- IDOR on customer and transaction views
- SSRF or webhook callback abuse
- injection in any search or import endpoints
- secret exposure in client-side bundles, docs, or error responses
- security headers and cookie flags
- rate limiting and anti-automation controls

## Sources

- https://status.dodopayments.com/
- https://docs.dodopayments.com/
- https://docs.dodopayments.com/developer-resources/sdks/cli
- https://www.scamadviser.com/check-website/dodopayments.com
