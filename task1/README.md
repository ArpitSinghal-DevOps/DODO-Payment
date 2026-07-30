# Task 1 - Deploy and Harden the Workload

## Objective

Deploy `ledger-api` and a neighbouring `reporting` workload in a local Kubernetes cluster with production-grade baseline controls.

The goal is not only to make the pod run. The goal is to reduce PCI-scope runtime risk, make insecure deployments fail early, and produce evidence an auditor or senior reviewer can inspect.

## Architecture

```text
Client
  |
  v
Ingress Controller
  |
  v
Service: ledger-api
  |
  v
Deployment: ledger-api
  |
  +-- ConfigMap: non-secret runtime config
  +-- Secret: created from Sealed Secrets or SOPS, not committed as plaintext

Deployment: reporting <--- controlled internal HTTP ---> Service: ledger-api

Pod Security Admission and Kyverno guard the Kubernetes API.
NetworkPolicy limits lateral movement inside the namespace.
```

## Why Each Component Exists

`Namespace`: `payments` isolates the workload and carries Pod Security Standard labels. `restricted` blocks privileged containers, host namespace sharing, and other risky pod settings.

`Deployment`: owns the desired state for each workload. It gives rolling updates, replica management, and rollback history.

`ReplicaSet`: created by the Deployment controller. We do not edit ReplicaSets directly because they are implementation details of Deployment reconciliation.

`Service`: gives stable DNS and load balancing for pods whose IPs change.

`ConfigMap`: stores non-sensitive runtime configuration such as `FLASK_ENV`, log level, and Python runtime flags.

`Secret`: stores sensitive runtime configuration. Plaintext Secret YAML is not committed because Kubernetes Secrets are only base64 encoded unless encryption and external secret management are added.

`ServiceAccount`: gives each workload a distinct identity. Both app ServiceAccounts disable token automount because the containers do not need Kubernetes API access.

`RBAC`: app pods receive no RoleBinding, which is least privilege. Bonus human persona Roles are included for developer, operator, and admin access patterns.

`Ingress`: exposes the service through a local ingress controller. Production would add TLS, DNS, WAF/rate limits, and stricter ingress annotations.

`SecurityContext`: locks the container down with no privilege escalation, read-only root filesystem, and all capabilities dropped.

`PodSecurityContext`: enforces non-root UID/GID and seccomp `RuntimeDefault` at pod level.

`Resource requests`: reserve capacity for scheduling and reduce noisy-neighbour risk.

`Resource limits`: cap runaway CPU/memory consumption.

`Startup probe`: prevents Kubernetes from killing a slow-starting container too early.

`Readiness probe`: controls whether a pod receives traffic.

`Liveness probe`: restarts a stuck process.

`Pod Security Standards`: built-in Kubernetes policy. `restricted` is the expected baseline for a payment workload.

`Admission Controllers`: reject bad objects before they enter the cluster.

`Kyverno`: Kubernetes-native policy engine used here to reject root containers, `:latest`, missing hardening fields, missing probes/resources, and unsigned GHCR images. The keyless image verification policy uses Kyverno v1.12-compatible `subject` and `issuer` fields for GitHub OIDC signatures and Rekor transparency log verification.

`OPA Gatekeeper`: good alternative for Rego-heavy organizations. I chose Kyverno because the assignment artifacts remain readable YAML.

`Sealed Secrets`: recommended local GitOps option. It encrypts a Secret for one cluster controller.

`SOPS`: strong alternative for encrypted files across environments using age/GPG/KMS.

`External Secrets`: best production pattern when backed by Vault or cloud secret managers.

## Files

- `task1/k8s/base/namespace.yaml`: namespace and Pod Security Standard labels.
- `task1/k8s/base/serviceaccounts.yaml`: dedicated workload identities with token automount disabled.
- `task1/k8s/base/configmap.yaml`: non-secret environment configuration.
- `task1/k8s/base/deployment-ledger-api.yaml`: hardened API workload.
- `task1/k8s/base/deployment-reporting.yaml`: hardened neighbour HTTP workload.
- `task1/k8s/base/services.yaml`: ClusterIP services for `ledger-api` and `reporting`.
- `task1/k8s/base/ingress.yaml`: local ingress route for `ledger-api.local`.
- `task1/k8s/base/networkpolicies.yaml`: default deny plus explicit allows.
- `task1/k8s/base/rbac-personas.yaml`: bonus least-privilege human persona Roles.
- `task1/policies/kyverno/*.yaml`: admission guardrails.
- `task1/secrets/secret-template.yaml`: non-production template only.
- `task1/tests/insecure-ledger-api.yaml`: negative test for policy rejection.

## Important YAML Fields

`replicas: 3`: keeps multiple API pods available during restarts and rolling updates.

`revisionHistoryLimit: 3`: keeps limited rollout history without accumulating old ReplicaSets.

`strategy.rollingUpdate`: allows controlled rollout with at most one unavailable and one surge pod.

`serviceAccountName`: prevents accidental use of the default ServiceAccount.

`automountServiceAccountToken: false`: removes unnecessary API credentials from the pod filesystem.

`runAsNonRoot: true`: makes root execution a runtime error.

`runAsUser` and `runAsGroup`: pin the process to a high non-system identity.

`fsGroup`: makes mounted volumes writable by the non-root process when needed.

`seccompProfile.type: RuntimeDefault`: enables the runtime syscall filter.

`allowPrivilegeEscalation: false`: blocks privilege escalation through setuid or file capabilities.

`readOnlyRootFilesystem: true`: prevents writes to the image filesystem.

`capabilities.drop: [ALL]`: removes unnecessary Linux privileges.

`emptyDir` mounted at `/tmp`: gives the app a bounded writable temp area while keeping the root filesystem read-only.

`resources.requests`: tells the scheduler what the pod needs.

`resources.limits`: caps resource abuse.

`startupProbe`, `readinessProbe`, `livenessProbe`: separate startup protection, traffic eligibility, and deadlock recovery.

`NetworkPolicy default-deny`: denies ingress and egress unless another policy allows it.

`namespaceSelector` for `ingress-nginx` and `kube-system`: allows ingress traffic and DNS without opening the namespace broadly.

## Security Implications

These manifests assume a compromised app process should not be able to become root, write persistent files, use unnecessary kernel capabilities, steal a Kubernetes token, freely scan the cluster, or bypass admission standards.

The remaining application-level risks are intentionally visible for later tasks: unsafe YAML loading, SSRF-capable `/fetch`, exposed PAN-like data, and old dependencies. Task 1 hardens runtime deployment; it does not pretend vulnerable code is safe.

## Install Tools

Kyverno is mandatory for this Task 1 implementation because admission policy is part of the assignment.

Problem solved: Kyverno prevents insecure Kubernetes objects from being admitted.

Why selected: it is Kubernetes-native YAML, easy to review, and simple to demo locally.

Alternatives: OPA Gatekeeper, ValidatingAdmissionPolicy, commercial policy engines.

Advantages: readable policies, mutate/validate/verify image support, strong Kubernetes integration.

Disadvantages: another controller to operate; policy syntax must be tested carefully.

Install:

```bash
kubectl create -f https://github.com/kyverno/kyverno/releases/download/v1.12.5/install.yaml
```

Verification:

```bash
kubectl -n kyverno get pods
kubectl get crd clusterpolicies.kyverno.io
```

Upgrade:

```bash
kubectl apply -f https://github.com/kyverno/kyverno/releases/download/v1.12.6/install.yaml
```

Removal:

```bash
kubectl delete -f https://github.com/kyverno/kyverno/releases/download/v1.12.5/install.yaml
```

Troubleshooting:

```bash
kubectl -n kyverno logs deploy/kyverno-admission-controller
kubectl get events -A --sort-by=.lastTimestamp
```

## Secret Handling

Mandatory: plaintext `STRIPE_API_KEY` and `DB_PASSWORD` must not be committed.

This implementation references `ledger-api-secrets` but does not commit live secret values. Use `task1/secrets/README.md` to generate a SealedSecret or SOPS-encrypted secret.

## Apply

Build the local image with a non-latest tag:

```bash
docker build -t ledger-api:0.1.0 ./app
```

Purpose: creates the image used by the hardened Deployment.

Expected output: successful Docker build and local image tag `ledger-api:0.1.0`.

Common errors: Docker daemon unavailable, base image pull failure, dependency install failure.

Create the namespace first:

```bash
kubectl apply -f task1/k8s/base/namespace.yaml
```

Create the secret through Sealed Secrets or a temporary local Secret for testing:

```bash
kubectl create secret generic ledger-api-secrets \
  --namespace payments \
  --from-literal=STRIPE_API_KEY='local-test-only' \
  --from-literal=DB_PASSWORD='local-test-only'
```

Apply the workload:

```bash
kubectl apply -k task1/k8s/base
```

Apply policies:

```bash
kubectl apply -f task1/policies/kyverno
```

Apply signed-image verification after Task 2 has produced signed GHCR images:

```bash
kubectl apply -f task1/policies/kyverno/verify-signed-images.yaml
```

Important: the signed-image policy only matches `ghcr.io/*/ledger-api:*`. The local image `ledger-api:0.1.0` is intentionally not matched so Task 1 can run locally before Task 2 creates signed images.

## Verification

Check workload state:

```bash
kubectl -n payments get pods,svc,ingress
```

Check probes and security context:

```bash
kubectl -n payments describe deploy ledger-api
```

Check ServiceAccount permissions:

```bash
kubectl -n payments auth can-i list pods --as=system:serviceaccount:payments:ledger-api
```

Expected output: `no`.

Port-forward service:

```bash
kubectl -n payments port-forward svc/ledger-api 8080:8080
```

Health check:

```bash
curl -i http://127.0.0.1:8080/health
```

Expected output: HTTP `200` and `{"status":"ok"}`.

Neighbour service test:

```bash
kubectl -n payments port-forward svc/reporting 8081:8080
curl -i http://127.0.0.1:8081/
```

Expected output: HTTP `200` and `{"service":"reporting","status":"ok"}`.

Policy rejection test:

```bash
kubectl apply -f task1/tests/insecure-ledger-api.yaml
```

Expected output: admission denied because the manifest uses `:latest` and lacks required hardening controls.

## Audit Readiness

Evidence to capture:

- `kubectl get ns payments --show-labels`
- `kubectl -n payments get deploy ledger-api -o yaml`
- `kubectl -n payments get sa ledger-api -o yaml`
- `kubectl -n payments auth can-i list pods --as=system:serviceaccount:payments:ledger-api`
- `kubectl -n payments get networkpolicy`
- `kubectl get clusterpolicy`
- failed apply output for `task1/tests/insecure-ledger-api.yaml`
- successful `/health` response
- screenshot of encrypted Secret workflow output, not plaintext secret values

## Rollback

Remove workload:

```bash
kubectl delete -k task1/k8s/base
```

Remove policies:

```bash
kubectl delete -f task1/policies/kyverno
```

Production impact: removing policies reopens the admission path for insecure workloads. Treat it as a controlled change.

## Common Mistakes

- Committing plaintext Secret YAML.
- Using `:latest` because it is convenient locally.
- Giving the app pod a RoleBinding even though it does not use the Kubernetes API.
- Enabling read-only root filesystem without providing `/tmp` when the runtime needs temporary writes.
- Forgetting DNS egress in a default-deny namespace.
- Applying signed-image enforcement before the CI pipeline signs images.

## Interview Questions

- Why is a Kubernetes Secret not safe to commit to git?
- Why should a pod not mount a ServiceAccount token by default?
- What is the difference between Pod Security Admission and Kyverno?
- What problem does a readiness probe solve that a liveness probe does not?
- Why are NetworkPolicies still useful if we later add Istio?
- What are the risks of `imagePullPolicy: Always` with mutable tags?
- How would you design RBAC for developers without giving production write access?

## Step Closeout

Summary: Task 1 introduces hardened workload manifests, namespace guardrails, NetworkPolicy, Kyverno policies, and a non-plaintext secret workflow.

What we learned: Kubernetes hardening is layered. Runtime settings, identity, network policy, secrets, and admission control solve different parts of the risk model.

Security concepts covered: least privilege, pod hardening, PSS restricted, admission control, non-root containers, immutable image tags, secret hygiene, and network segmentation.

Best practices: keep insecure examples separate, use non-latest tags, deny by default, bind no RBAC unless needed, and generate audit evidence.

Production considerations: replace local image tags with signed GHCR digest references, use a real secret manager, add TLS at ingress, and monitor policy violations.

What to commit to Git: `task1/` artifacts and `.gitignore`; do not commit `venv/`, plaintext secrets, decrypted files, or private keys.

Screenshots to capture: namespace labels, pods ready, security context, policies installed, policy rejection, successful health check, and secret encryption flow.

README updates: link this Task 1 README from the top-level README after all tasks are organized.

Next verification checklist: run Kustomize render, apply to cluster, create sealed secret, test service, test policy rejection.

Next task preview: Task 2 will build, scan, sign, attest, and deploy through GitHub Actions and GitOps.
