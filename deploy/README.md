# Deploying Ploidy

Two supported paths:

## Helm chart

```sh
helm install ploidy deploy/helm/ploidy \
    --set-string secrets.PLOIDY_AUTH_TOKEN=$(openssl rand -hex 24) \
    --set image.tag=0.3.3
```

Switches worth knowing:

- `persistence.size` — grow the PVC when retention is off and history builds up.
- `env.PLOIDY_RETENTION_DAYS` — enable periodic purge (the service also exposes
  an ad-hoc `python -m ploidy.retention purge --days N`).
- `serviceMonitor.enabled` — scrape `GET /metrics` via kube-prometheus-stack.
- `networkPolicy.enabled` — lock ingress to the same namespace plus
  `networkPolicy.allowFromNamespaces` (e.g. `["monitoring"]`).
- `secrets` vs `existingSecret` — pre-create a Secret externally (e.g. via
  external-secrets/SOPS) and point `existingSecret` at it.

Tokens expected in the Secret when using `existingSecret`:

- `PLOIDY_AUTH_TOKEN` — single-tenant bearer token
- `PLOIDY_TOKENS` — multi-tenant JSON map `{"tok-a": "tenant-a"}`
- `PLOIDY_API_KEY` — for `debate_auto` when using the OpenAI-compatible
  fallback
- `PLOIDY_DASH_TOKEN` — dashboard bearer token

## Plain kubectl

```sh
kubectl apply -f deploy/kubernetes/ploidy.yaml
```

The single-file manifest is deliberately minimal (no ServiceMonitor / NetworkPolicy).
Edit the embedded Secret before applying if you want auth enabled.

## Scaling note

Both layouts fix `replicas: 1` and use the `Recreate` strategy. The state
backend is a local SQLite file mounted on a PVC, so two pods would corrupt
each other's writes. The Redis-backed backend that unblocks horizontal scale
is tracked as a separate follow-up.
