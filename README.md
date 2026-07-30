<<<<<<< HEAD
# ledger-api

Payments microservice for tokenising PANs and serving transaction metadata.
Deployed on Kubernetes in the `payments` namespace.

## DevSecOps Assignment

- [Task 1 - Deploy and Harden the Workload](task1/README.md)
- [Task 2 - Build, Scan, Sign, Attest, and Deploy](task2/README.md)

## Endpoints

| Method | Path            | Description                          |
|--------|-----------------|--------------------------------------|
| GET    | `/health`       | Liveness check                       |
| POST   | `/tokenize`     | `{"pan": "..."}` → opaque token      |
| GET    | `/transactions` | Recent transaction records           |
| POST   | `/import`       | Import a YAML configuration blob     |
| GET    | `/fetch?url=`   | Fetch a remote resource by URL       |
=======
# DODO-Payment
DODO Payment for Security &amp; DevOps Engineer 
>>>>>>> 0c107b1a7b88680517a539c4fd38a71be7099169
