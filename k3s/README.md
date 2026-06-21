# K3s Deployment for jktlug.id

These manifests deploy the **jktlug.id** static site to a [K3s](https://k3s.io/) cluster using the production Docker image built by GitHub Actions and pushed to GitHub Container Registry (GHCR).

## Files

| File | Purpose |
|------|---------|
| `namespace.yaml` | Isolates the application in its own namespace (`jktlug`). |
| `deployment.yaml` | Runs the site container with rolling updates, probes, and resource limits. |
| `service.yaml` | Exposes the deployment inside the cluster via `ClusterIP`. |
| `ingress.yaml` | Routes external traffic from `jktlug.id` / `www.jktlug.id` to the service. |
| `hpa.yaml` | Automatically scales replicas based on CPU/memory utilization. |
| `pdb.yaml` | Ensures at least one pod stays available during node maintenance. |

## Prerequisites

1. A running K3s cluster (single-node or multi-node).
2. The GitHub Actions CI/CD workflow has pushed an image to GHCR:
   ```
   ghcr.io/jktlug/jktlug.id:latest
   ```
3. DNS A/AAAA records pointing `jktlug.id` and `www.jktlug.id` to your K3s node(s) or a load balancer in front of them.
4. (Optional) If the GHCR image is **private**, create a pull secret first:
   ```bash
   kubectl create secret docker-registry ghcr-pull-secret \
     --namespace jktlug \
     --docker-server=ghcr.io \
     --docker-username=<GITHUB_USERNAME> \
     --docker-password=<GITHUB_PERSONAL_ACCESS_TOKEN>
   ```
   Then uncomment the `imagePullSecrets` block in `deployment.yaml`.

## Quick start

```bash
# Apply all manifests
kubectl apply -f k3s/

# Watch the rollout
kubectl rollout status deployment/jktlug-website -n jktlug

# Verify pods are running
kubectl get pods -n jktlug

# Check the ingress
kubectl get ingress -n jktlug
```

## K3s-specific notes

### Ingress controller
K3s ships with **Traefik** by default. The provided `ingress.yaml` uses a standard `networking.k8s.io/v1` Ingress resource, which Traefik supports natively. If you disabled Traefik and installed **nginx-ingress** instead, swap the annotations in `ingress.yaml` as commented.

### TLS / Let's Encrypt
To enable automatic HTTPS with Let's Encrypt on K3s, the easiest path is to install **cert-manager** and add a `ClusterIssuer`. Then uncomment the `tls` block in `ingress.yaml` and reference your TLS secret:

```yaml
tls:
  - hosts:
      - jktlug.id
      - www.jktlug.id
    secretName: jktlug-tls
```

### Local testing without real DNS
If you are testing locally (e.g., on a single-node K3s VM), you can skip the Ingress and expose the Service directly with a LoadBalancer:

```bash
# Change service.yaml type to LoadBalancer
kubectl patch svc jktlug-website -n jktlug -p '{"spec":{"type":"LoadBalancer"}}'

# Wait for K3s Klipper LB to assign a node IP
kubectl get svc jktlug-website -n jktlug
```

Or use port-forward for quick verification:

```bash
kubectl port-forward -n jktlug svc/jktlug-website 8080:80
# open http://localhost:8080
```

## Updating the site

When the CI/CD pipeline pushes a new image to GHCR, the deployment will pick it up on the next sync (if using GitOps) or you can force a rolling restart:

```bash
kubectl rollout restart deployment/jktlug-website -n jktlug
```

For a more GitOps-friendly approach, pin the image to a specific commit SHA in `deployment.yaml` and update the manifest (or use a tool like ArgoCD / Flux) when the CI pipeline completes.
