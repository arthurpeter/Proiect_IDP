#!/bin/bash

echo "🔍 Detectare sistem de operare..."

# 1. Identificare Manager de Pachete
if command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="sudo dnf install -y"
    KUBECTL_PKG="kubernetes-client"
    DOCKER_PKG="moby-engine" # Pachetul standard pe Fedora
elif command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
    INSTALL_CMD="sudo apt-get update && sudo apt-get install -y"
    KUBECTL_PKG="kubectl"
    DOCKER_PKG="docker.io" # Pachetul standard pe Ubuntu
else
    echo "❌ Manager de pachete nesuportat."
    exit 1
fi

# 2. Verificare și instalare Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Docker nu este instalat. Se instalează $DOCKER_PKG..."
    $INSTALL_CMD $DOCKER_PKG
    sudo systemctl enable --now docker
    # Adăugăm utilizatorul în grupul docker pentru a nu mai folosi sudo ulterior
    sudo usermod -aG docker $USER
    echo "⚠️ Docker a fost instalat. S-ar putea să fie nevoie de logout/login pentru permisiuni."
else
    echo "✅ Docker este instalat."
fi

# 3. Pornire serviciu Docker dacă este oprit
if ! systemctl is-active --quiet docker; then
    echo "⚙️ Pornire serviciu Docker..."
    sudo systemctl start docker
fi

# 4. Verificare permisiuni Docker (evită eroarea de socket)
if ! docker info &> /dev/null; then
    echo "🔑 Se repară permisiunile Docker socket..."
    sudo chmod 666 /var/run/docker.sock
    
    # Re-verificare după reparație
    if ! docker info &> /dev/null; then
        echo "❌ Eroare critică: Tot nu se poate accesa Docker API după reparație."
        exit 1
    fi
fi
echo "✅ Docker API este accesibil."

# 5. Instalare kubectl
if ! command -v kubectl &> /dev/null; then
    echo "📦 Instalare kubectl..."
    $INSTALL_CMD $KUBECTL_PKG
fi

# 6. Instalare kind
if ! command -v kind &> /dev/null; then
    echo "📦 Instalare kind..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# 6.5 Instalare Helm
if ! command -v helm &> /dev/null; then
    echo "📦 Instalare Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# 7. Cluster kind
CLUSTER_NAME="remailder-cluster"
if ! kind get clusters | grep -q "^$CLUSTER_NAME$"; then
    echo "🏗️ Creare cluster kind..."
    kind create cluster --name "$CLUSTER_NAME"
fi

# 7.5 Instalare Loki Stack (Loki + Promtail + Grafana + Prometheus)
if ! helm list | grep -q "loki"; then
    echo "📊 Instalare Stack de Logging și Monitorizare..."
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    helm upgrade --install loki grafana/loki-stack \
        --set grafana.enabled=true \
        --set prometheus.enabled=true \
        --set loki.persistence.enabled=false \
        --set prometheus.server.persistentVolume.enabled=false \
        --set grafana.sidecar.dashboards.enabled=true \
        --set grafana.sidecar.dashboards.label=grafana_dashboard \
        --set grafana.sidecar.dashboards.labelValue="1" \
        --set grafana.sidecar.dashboards.searchNamespace=ALL
fi

# 7.6 Încărcare automată Dashboard
echo "📥 Încărcare dashboard preconfigurat..."
kubectl delete configmap remailder-dashboards --ignore-not-found
kubectl create configmap remailder-dashboards --from-file=kubernetes/infra/dashboards/final-dashboard.json
kubectl label configmap remailder-dashboards grafana_dashboard=1

# 8. Curățare porturi și Secrete
sudo fuser -k 8000/tcp 8001/tcp 5432/tcp 15672/tcp 8080/tcp 3000/tcp 2>/dev/null
pkill -f "kubectl port-forward" 2>/dev/null

if [ ! -f .env ]; then
    echo "❌ Lipsește fișierul .env!"
    exit 1
fi

kubectl delete secret postgres-secrets --ignore-not-found
kubectl create secret generic postgres-secrets --from-env-file=.env

# 9. Aplicare Manifeste K8s
kubectl apply -f kubernetes/infra/postgres-pvc.yaml
kubectl apply -f kubernetes/infra/postgres.yaml
kubectl apply -f kubernetes/infra/adminer.yaml
kubectl apply -f kubernetes/infra/rabbitmq.yaml
kubectl apply -f kubernetes/apps/io-service.yaml
kubectl rollout restart deployment io-service
kubectl apply -f kubernetes/apps/main-service.yaml
kubectl rollout restart deployment main-service

# 10. Așteptare și Port-forward
echo "⏳ Așteptare Pod-uri..."
kubectl wait --for=condition=ready pod -l app=io-service --timeout=180s
kubectl wait --for=condition=ready pod -l app=main-service --timeout=180s
echo "⏳ Așteptare Grafana (poate dura câteva minute la prima rulare)..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana --timeout=300s
kubectl port-forward svc/io-service 8000:8000 > /dev/null 2>&1 &
kubectl port-forward svc/main-service 8001:8001 > /dev/null 2>&1 &
kubectl port-forward svc/postgres-db 5432:5432 > /dev/null 2>&1 &
kubectl port-forward svc/rabbitmq-service 15672:15672 > /dev/null 2>&1 &
kubectl port-forward svc/adminer-service 8080:8080 > /dev/null 2>&1 &
kubectl port-forward svc/loki-grafana 3000:80 > /dev/null 2>&1 &

GRAFANA_PASS=$(kubectl get secret loki-grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
echo "✨ Setup finalizat!"
echo "📊 Grafana: http://localhost:3000 (User: admin | Pass: $GRAFANA_PASS)"