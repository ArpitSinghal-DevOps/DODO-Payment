# Production GitOps Overlay

This overlay reuses the hardened Task 1 Kubernetes base and replaces the local `ledger-api:0.1.0` image with an immutable GHCR image produced by the Task 2 workflow.

Update before applying:

```bash
kustomize edit set image ledger-api=ghcr.io/<owner>/ledger-api:sha-<commit>
```

Prefer digest pinning for production:

```bash
kustomize edit set image ledger-api=ghcr.io/<owner>/ledger-api@sha256:<digest>
```

Render check:

```bash
kubectl kustomize task2/gitops/overlays/prod
```
