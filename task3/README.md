# Task 3 - Istio and Zero Trust

## Objective

Bring `ledger-api` and its neighbour into an Istio service mesh, enforce mutual TLS, lock access down by workload identity, and add Kubernetes NetworkPolicy underneath for defense in depth.

This task is about identity, not IP. The point is to make the service accept traffic only from explicitly trusted workloads and to refuse plaintext paths that bypass the mesh.

## Architecture

```text
Client / Rogue Pod / Reporting Pod
  |
  v
Istio sidecar proxy (Envoy)
  |
  v
ledger-api Service -> ledger-api Pod

Istio control plane (istiod) issues workload certificates and rotates them.
PeerAuthentication enforces mTLS.
AuthorizationPolicy decides who may talk to ledger-api.
DestinationRule tells clients to use ISTIO_MUTUAL for ledger-api.
NetworkPolicy blocks non-mesh lateral movement and constrains control-plane paths.
```

## Why Each Component Exists

`Istio control plane` (`istiod`) distributes configuration, issues workload certificates, and rotates them before expiry. The trust root is the Istio root certificate installed with the control plane. Workload identities are derived from SPIFFE-style service account identities such as `cluster.local/ns/payments/sa/reporting`.

`Envoy sidecar` enforces mesh policy at the pod edge. It handles mTLS, telemetry, retries, routing, and authz checks.

`Sidecar injection` adds the proxy to new pods in the namespace. Without injection, a workload cannot participate in sidecar-mode mTLS and policy evaluation.

`PeerAuthentication` in `STRICT` mode rejects plaintext traffic and requires an mTLS tunnel. This is the control that prevents a pod from bypassing the mesh with plain HTTP.

`AuthorizationPolicy` enforces identity-based access control. We use workload identities, not IP addresses, because IPs are fragile, spoofable in design discussions, and meaningless once pods reschedule.

`DestinationRule` configures client-side TLS origination. `ISTIO_MUTUAL` tells Istio clients to use Istio-issued certificates when calling `ledger-api`.

`NetworkPolicy` is still required because mesh policy is not a full replacement for Kubernetes network isolation. It prevents unexpected east-west paths and keeps control-plane connectivity explicit.

## Threat Model

Threats we are blocking:

- plaintext calls from non-meshed pods
- lateral movement from unauthorized meshed pods
- IP-based bypasses caused by pod rescheduling
- accidental exposure of `ledger-api` outside the mesh boundary
- uncontrolled control-plane traffic from sidecars

Threats the mesh does not solve alone:

- vulnerable application code
- SSRF in application logic
- stolen Kubernetes credentials
- compromised cluster nodes
- compromised Istio control plane

## Files

- `task3/istio/kustomization.yaml`: Task 3 overlay that layers mesh policy on top of the Task 1 base.
- `task3/istio/namespace-patch.yaml`: enables sidecar injection for the `payments` namespace.
- `task3/istio/peerauthentication.yaml`: enforces STRICT mTLS.
- `task3/istio/authorizationpolicy.yaml`: default-deny posture plus explicit allow by workload identity.
- `task3/istio/destinationrule.yaml`: forces `ISTIO_MUTUAL` for `ledger-api`.
- `task3/istio/networkpolicies.yaml`: allows Istio control-plane traffic while keeping default deny.
- `task3/tests/plaintext-client.yaml`: non-meshed client used to prove plaintext is refused.
- `task3/tests/rogue-client.yaml`: meshed but unauthorized client used to prove authz denial.

## Installation

What it solves: installs the Istio control plane into the local cluster so the mesh manifests have something to talk to.

Why selected: `istioctl install` is the supported, production-oriented installer and matches the assignment.

Alternative: Helm charts. I am not using them here because `istioctl` gives stronger validation and simpler operator experience for this task.

Advantages: versioned control-plane install, built-in validation, easier mesh bootstrap.

Disadvantages: another binary to manage, and cluster prerequisites must be satisfied.

Install the default profile:

```bash
istioctl install --set profile=default -y
```

Verify control plane:

```bash
kubectl -n istio-system get pods
istioctl verify-install
```

If you want to pre-render the install manifest instead of applying directly:

```bash
istioctl manifest generate --set profile=default > /tmp/istio-install.yaml
```

## Apply Order

1. Install Istio.
2. Label the `payments` namespace for sidecar injection.
3. Apply the Task 3 overlay.
4. Restart the `payments` workloads so sidecars are injected.
5. Apply the plaintext and rogue client test manifests.
6. Verify mTLS and authz behavior.

Namespace label command:

```bash
kubectl label namespace payments istio-injection=enabled --overwrite
```

Apply the mesh overlay:

```bash
kubectl apply -k task3/istio
```

## Important YAML Fields

`Namespace.metadata.labels.istio-injection: enabled`: enables automatic injection for new pods in `payments`.

`PeerAuthentication.spec.mtls.mode: STRICT`: refuses plaintext and requires mTLS.

`AuthorizationPolicy.spec.action: DENY` with `notPrincipals`: denies everything except the approved identities.

`AuthorizationPolicy.spec.action: ALLOW` with `principals`: explicitly permits only the trusted workload identities.

`DestinationRule.trafficPolicy.tls.mode: ISTIO_MUTUAL`: makes client proxies use Istio-issued certs for `ledger-api`.

`NetworkPolicy` egress rule to `istio-system` on `15012`: allows sidecars to talk to `istiod` for xDS and certificate work.

## Security Implications

`STRICT` mTLS means a pod without a sidecar or without a valid workload certificate cannot successfully talk to `ledger-api`.

The authz policy is identity-based. If a pod is rescheduled, its IP changes, but its service account identity remains stable. That is why the policy is resilient.

The extra NetworkPolicy layer matters because a mesh policy only governs traffic that makes it to Envoy. NetworkPolicy still blocks unexpected pod-to-pod paths and keeps the control plane edges explicit.

## How Certificates Work

Istio issues a workload certificate to each meshed pod based on its Kubernetes service account identity. The identity is represented as a SPIFFE-style principal.

Certificates are short-lived and rotated automatically by the Istio agent before expiry. That limits blast radius if a cert is exposed.

The trust root is the Istio root CA installed with the control plane. Workload certs chain back to that root.

## Verification

Check injection:

```bash
istioctl experimental check-inject -n payments deploy/ledger-api
kubectl -n payments get pod -l app.kubernetes.io/name=ledger-api
```

Expected result: the pod shows `2/2` containers once the sidecar is injected.

Check authz propagation:

```bash
istioctl x authz check deploy/ledger-api -n payments
```

Check strict mTLS:

```bash
istioctl authn tls-check deploy/reporting ledger-api.payments.svc.cluster.local
```

Check proxy certificates:

```bash
kubectl -n payments exec deploy/ledger-api -c istio-proxy -- ls /var/run/secrets/istio
```

Plaintext refusal test:

```bash
kubectl apply -f task3/tests/plaintext-client.yaml
kubectl -n legacy exec deploy/plain-client -- curl -sS -o /dev/null -w '%{http_code}\n' http://ledger-api.payments.svc.cluster.local:8080/health
```

Expected result: the request fails because the client is not in the mesh and cannot satisfy STRICT mTLS.

Unauthorized meshed client test:

```bash
kubectl apply -f task3/tests/rogue-client.yaml
kubectl -n attack exec deploy/rogue-client -- curl -sS -o /dev/null -w '%{http_code}\n' http://ledger-api.payments.svc.cluster.local:8080/health
```

Expected result: Istio denies the request with `403` because the workload identity is not on the allow list.

Authorized client test:

```bash
kubectl -n payments exec deploy/reporting -- python - <<'PY'
import urllib.request
print(urllib.request.urlopen('http://ledger-api:8080/health').read().decode())
PY
```

Expected result: the request succeeds because the `reporting` service account is allowed.

## Screenshots To Capture

- `kubectl get ns payments --show-labels`
- `kubectl -n payments get pods` showing `2/2` on meshed pods
- `kubectl -n payments get peerauthentication,authorizationpolicy,destinationrule`
- `istioctl x authz check deploy/ledger-api -n payments`
- `istioctl authn tls-check deploy/reporting ledger-api.payments.svc.cluster.local`
- plaintext client failure output
- rogue client `403` output
- successful reporting call to `ledger-api`

## Troubleshooting

If pods stay at `1/1`, the namespace may not have been labeled for injection or the pod needs a restart.

If you see `503` after adding `DestinationRule`, check that the TLS mode is `ISTIO_MUTUAL` and that both client and server are in the mesh.

If `kubectl` output shows `Connection reset by peer` for plaintext traffic, that is expected under STRICT mTLS.

## Rollback

Remove the Task 3 overlay:

```bash
kubectl delete -k task3/istio
```

Remove the namespace injection label only after all pods are restarted out of the mesh:

```bash
kubectl label namespace payments istio-injection-
```

Remove Istio from the cluster only after you no longer need the mesh controls or screenshots.

## Common Mistakes

- labeling the namespace for injection but forgetting to restart pods
- using IP-based authz instead of service account identity
- forgetting the egress path to `istiod`
- adding a `DestinationRule` with the wrong TLS mode and causing 503s
- assuming NetworkPolicy alone provides identity-aware zero trust

## Interview Questions

- What does `STRICT` mTLS block that `PERMISSIVE` does not?
- Why is SPIFFE identity better than IP addresses for authz?
- What is the relationship between PeerAuthentication and DestinationRule?
- Why can a NetworkPolicy not replace Istio authz?
- Why do workload certificates need rotation?
- What is the trust root in an Istio mesh?

## Commit and Documentation Notes

What to commit: `task3/README.md`, `task3/istio/*`, `task3/tests/*`, and the top-level README update.

What not to commit: any generated TLS private keys, temporary certs, or decrypted secret material.

Recommended commit message:

```text
task3: add istio zero-trust mesh policies and verification docs
```

## Next Verification Checklist

1. Start Minikube if it is not already running.
2. Install Istio with `istioctl install --set profile=default -y`.
3. Label `payments` for injection.
4. Apply `task3/istio`.
5. Restart the `payments` deployments.
6. Apply the plaintext and rogue client test manifests.
7. Run the mesh verification commands.
8. Capture screenshots for the report.

## Next Task Preview

Task 4 will switch to reconnaissance and authorized penetration testing. That work is separate from the mesh boundary and should use the documented rules of engagement.
