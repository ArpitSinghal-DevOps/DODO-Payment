# Task 1 Secret Workflow

Plaintext secrets must not be committed.

The app expects a Secret named `ledger-api-secrets` in namespace `payments`.

Required keys:

- `STRIPE_API_KEY`
- `DB_PASSWORD`

## Sealed Secrets Option

What it solves: Sealed Secrets lets us commit encrypted Kubernetes Secret material without exposing plaintext to git. Only the controller in the target cluster can decrypt it.

Why selected: it is easy to demonstrate locally and fits the assignment's GitOps-style requirement.

Alternatives: SOPS+age for encrypted YAML, External Secrets Operator for syncing from Vault or a cloud secret manager.

Install the controller:

```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.27.2/controller.yaml
```

Verification:

```bash
kubectl -n kube-system get pods -l name=sealed-secrets-controller
```

Create a temporary plaintext Secret outside the repo:

```bash
kubectl create secret generic ledger-api-secrets \
  --namespace payments \
  --from-literal=STRIPE_API_KEY='replace-me' \
  --from-literal=DB_PASSWORD='replace-me' \
  --dry-run=client -o yaml > /tmp/ledger-api-secret.yaml
```

Encrypt it for the cluster:

```bash
kubeseal --format yaml < /tmp/ledger-api-secret.yaml > task1/secrets/sealedsecret.yaml
```

Apply it:

```bash
kubectl apply -f task1/secrets/sealedsecret.yaml
```

Remove the temporary plaintext file:

```bash
shred -u /tmp/ledger-api-secret.yaml
```

Upgrade: upgrade the controller by applying the newer upstream release manifest and rotate sealed secrets if the sealing key changes.

Removal: delete the controller only after migrating secrets elsewhere, otherwise existing SealedSecret objects will not reconcile.

Troubleshooting: check controller logs, confirm namespace/name match, and confirm the Secret appears after the SealedSecret is applied.

## SOPS + age Option

Use this when you want environment-portable encrypted YAML in git.

```bash
age-keygen -o key.txt
sops --age "$(grep public key.txt | awk '{print $4}')" --encrypt secret-template.yaml > secret.enc.yaml
sops --decrypt secret.enc.yaml | kubectl apply -f -
```

Never commit `key.txt` or decrypted files.
