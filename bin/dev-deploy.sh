#!/usr/bin/env bash
# Local dev loop: rebuild the site image, load it into k3s, roll out the dev deployment.
#
# Usage:
#   bin/dev-deploy.sh             # rebuild site, image, import, roll out
#   bin/dev-deploy.sh --skip-site # skip `stack exec site-compiler build`
#
# Requires: docker, stack, kubectl, and sudo for `k3s ctr images import`.
set -euo pipefail

cd "$(dirname "$0")/.."

IMAGE="docker.io/library/jktlug-website:dev"
NAMESPACE="jktlug-dev"

if [[ "${1:-}" != "--skip-site" ]]; then
    if ! command -v stack >/dev/null 2>&1; then
        echo "!! 'stack' not found on PATH. Either:"
        echo "   - install it:  curl -sSL https://get.haskellstack.org/ | sh"
        echo "   - or rerun with --skip-site to reuse the existing _site/"
        exit 1
    fi
    echo "==> Building site (_site/)"
    stack exec site-compiler build
fi

echo "==> Building image $IMAGE"
docker build -f Dockerfile.runtime -t "$IMAGE" .

echo "==> Importing image into k3s containerd (may prompt for sudo password)"
# Resolve the full path: sudo's secure_path may not include /usr/local/bin
K3S_BIN="$(command -v k3s || echo /usr/local/bin/k3s)"
docker save "$IMAGE" | sudo "$K3S_BIN" ctr images import -

echo "==> Applying k3s/dev manifests"
kubectl apply -f k3s/dev/

echo "==> Rolling out"
kubectl rollout restart deployment/jktlug-website -n "$NAMESPACE"
kubectl rollout status deployment/jktlug-website -n "$NAMESPACE"

TRAEFIK_IP="$(kubectl get svc traefik -n kube-system \
    -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"

cat <<EOF

==> Done. Access the dev site via:

    # Option A: port-forward (no setup)
    kubectl port-forward -n $NAMESPACE svc/jktlug-website 8080:80
    # then open http://localhost:8080

    # Option B: ingress via Traefik
    # add this line to /etc/hosts:
    ${TRAEFIK_IP:-<traefik-ip>}  JKTLUG.local
    # then open http://JKTLUG.local
EOF
