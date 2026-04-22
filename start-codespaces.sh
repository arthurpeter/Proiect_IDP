#!/bin/bash
echo "🚀 Pornire setup complet pentru Home Server (k3d: 1 Manager + 2 Workers)..."

# 1. Instalare utilitare de bază
echo "🔍 Verificare utilitare necesare..."
if ! command -v curl &> /dev/null || ! command -v fuser &> /dev/null || ! command -v pkill &> /dev/null; then
    sudo apt-get update && sudo apt-get install -y curl psmisc
fi

# 2. Instalare Docker (K3d are nevoie de Docker)
if ! command -v docker &> /dev/null; then
    echo "📦 Instalare Docker..."
    sudo apt-get install -y docker.io
    sudo systemctl enable --now docker
    sudo usermod -aG docker $USER
    sudo chmod 666 /var/run/docker.sock
fi

# 3. Instalare Helm
if ! command -v helm &> /dev/null; then
    echo "📦 Instalare Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# 4. Instalare k3d
if ! command -v k3d &> /dev/null; then
    echo "📦 Instalare k3d..."
    curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
fi

# 4.5 Instalare kubectl (dacă lipsește)
if ! command -v kubectl &> /dev/null; then
    echo "📦 Instalare kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm kubectl
fi

# 5. Creare Cluster Kubernetes (1 Manager, 2 Workers)
CLUSTER_NAME="proiect-cluster"
if k3d cluster list | grep -q "$CLUSTER_NAME"; then
    echo "✅ Clusterul k3d '$CLUSTER_NAME' există deja."
else
    echo "🏗️ Creare cluster Kubernetes cu 3 noduri (1 Manager + 2 Workers)..."
    # Folosim --k3s-arg pentru a dezactiva Traefik (deoarece tu folosești Kong Gateway)
    k3d cluster create $CLUSTER_NAME --servers 1 --agents 2 --k3s-arg "--disable=traefik@server:*"
    echo "⏳ Așteptăm pornirea clusterului..."
    sleep 15
fi

# k3d configurează automat ~/.kube/config, ne asigurăm doar că exportul e corect
export KUBECONFIG=~/.kube/config

# 6. Verificare .env și creare secrete
if [ ! -f .env ]; then
    echo "❌ Lipsește fișierul .env! Asigură-te că este în același folder cu scriptul."
    exit 1
fi
kubectl delete secret postgres-secrets --ignore-not-found
kubectl create secret generic postgres-secrets --from-env-file=.env

# 7. Instalare Stack Monitorizare (Loki, Grafana, Prometheus - Optimizat pt RAM puțin)
if ! helm list | grep -q "loki"; then
    echo "📊 Instalare Stack de Logging și Monitorizare (mod de economisire memorie)..."
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    helm upgrade --install loki grafana/loki-stack \
        --set grafana.enabled=true \
        --set prometheus.enabled=true \
        --set prometheus.server.global.scrape_interval=1m \
        --set prometheus.server.retention=1d \
        --set loki.persistence.enabled=false \
        --set prometheus.server.persistentVolume.enabled=false \
        --set grafana.sidecar.dashboards.enabled=true \
        --set grafana.sidecar.dashboards.label=grafana_dashboard \
        --set grafana.sidecar.dashboards.labelValue="1" \
        --set grafana.sidecar.dashboards.searchNamespace=ALL
fi

# 8. Încărcare automată Dashboard în Grafana
echo "📥 Încărcare dashboard preconfigurat..."
kubectl delete configmap remailder-dashboards --ignore-not-found
kubectl create configmap remailder-dashboards --from-file=kubernetes/infra/dashboards/final-dashboard.json
kubectl label configmap remailder-dashboards grafana_dashboard=1

# 9. Curățare port-forwarding vechi
echo "🧹 Eliberare porturi de rețea..."
sudo fuser -k 8000/tcp 8001/tcp 8002/tcp 5432/tcp 15672/tcp 8080/tcp 3000/tcp 3001/tcp 8443/tcp 9000/tcp 2>/dev/null
pkill -f "kubectl port-forward" 2>/dev/null

# 10. Aplicare Manifeste K8s
echo "🏗️ Aplicare arhitectură microservicii..."
kubectl apply -f kubernetes/infra/postgres-pvc.yaml
kubectl apply -f kubernetes/infra/postgres.yaml
kubectl apply -f kubernetes/infra/adminer.yaml
kubectl apply -f kubernetes/infra/rabbitmq.yaml
kubectl apply -f kubernetes/apps/io-service.yaml
kubectl apply -f kubernetes/apps/main-service.yaml
kubectl apply -f kubernetes/apps/auth-deploy.yaml
kubectl apply -f kubernetes/apps/front-deploy.yaml
kubectl apply -f kubernetes/infra/kong-gateway.yaml
kubectl apply -f kubernetes/infra/portainer.yaml
kubectl apply -f kubernetes/infra/network-topology.yaml

# 11. Așteptare Pod-uri să fie Ready
echo "⏳ Așteptare pornire microservicii (Acest pas folosește Swap-ul, ai răbdare)..."
kubectl wait --for=condition=ready pod -l app=kong-gateway --timeout=300s
kubectl wait --for=condition=ready pod -l app=frontend-ui --timeout=300s
echo "⏳ Așteptare Grafana..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana --timeout=400s

# 12. Configurare Port-Forwarding Expus Public (--address 0.0.0.0)
echo "🔌 Mapare porturi pe interfața locală a rețelei..."
kubectl port-forward --address 0.0.0.0 svc/kong-gateway 8443:8000 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/frontend-ui 3001:80 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/portainer-service 9000:9000 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/adminer-service 8080:8080 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/rabbitmq-service 15672:15672 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/loki-grafana 3000:80 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/postgres-db 5432:5432 > /dev/null 2>&1 &

# 13. Aflare variabile finale
GRAFANA_PASS=$(kubectl get secret loki-grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
DB_PASS=$(grep POSTGRES_PASSWORD .env | cut -d '=' -f2)
IP_LOCAL=$(hostname -I | awk '{print $1}')

echo ""
echo "═══════════════════════════════════════════════════"
echo "✨ CLUSTER K3D (3 NODURI) PORNIT CU SUCCES! ✨"
echo "Pentru a demonstra profesorului arhitectura, rulează:"
echo "   kubectl get nodes"
echo ""
echo "Folosește link-urile de mai jos din browserul PC-ului tău:"
echo "🌐 Frontend UI:   https://$IP_LOCAL:3001"
echo "🚪 Kong Gateway:  https://$IP_LOCAL:8443"
echo "📊 Grafana:       https://$IP_LOCAL:3000 (User: admin | Pass: $GRAFANA_PASS)"
echo "🗄️  Adminer:       https://$IP_LOCAL:8080 (Server: postgres-db | User: remailder_admin | Pass: $DB_PASS | DB: remailder_db)"
echo "📦 Portainer:     https://$IP_LOCAL:9000"
echo "🐇 RabbitMQ:      https://$IP_LOCAL:15672 (User: guest | Pass: guest)"
echo "═══════════════════════════════════════════════════"
