#!/bin/bash

echo "🌐 Inițializare mediu Killercoda Kubernetes..."

# 1. Verificăm dacă avem deja clusterul (Killercoda îl oferă automat)
echo "✅ Se folosește clusterul preconfigurat Killercoda:"
kubectl get nodes

# 2. Instalare Helm (Uneori e preinstalat pe Killercoda, dar ne asigurăm)
if ! command -v helm &> /dev/null; then
    echo "📦 Se instalează Helm..."
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    bash get_helm.sh
fi

# 3. Instalare StorageClass pentru baza de date
echo "💾 Se instalează Local Path Provisioner (Necesar pentru Postgres pe cloud)..."
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.26/deploy/local-path-storage.yaml
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# 4. Instalare Stack de Monitorizare (Loki & Grafana)
if ! helm list -A | grep -q "loki"; then
    echo "📊 Instalare Stack de Logging și Monitorizare (Grafana/Loki)..."
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

# 5. Încărcare automată Dashboard Grafana
echo "📥 Încărcare dashboard preconfigurat..."
kubectl delete configmap remailder-dashboards --ignore-not-found
kubectl create configmap remailder-dashboards --from-file=kubernetes/infra/dashboards/final-dashboard.json
kubectl label configmap remailder-dashboards grafana_dashboard=1

# 6. Verificare și creare Secrete
if [ ! -f .env ]; then
    echo "❌ Lipsește fișierul .env! Creează-l înainte să rulezi scriptul."
    exit 1
fi

kubectl delete secret postgres-secrets --ignore-not-found
kubectl create secret generic postgres-secrets --from-env-file=.env

# 7. Curățare procese vechi de port-forwarding
pkill -f "kubectl port-forward" 2>/dev/null

# 8. Aplicare Manifeste K8s
echo "🚀 Se aplică infrastructura și microserviciile..."
kubectl apply -f kubernetes/infra/postgres-pvc.yaml
kubectl apply -f kubernetes/infra/postgres.yaml
kubectl apply -f kubernetes/infra/adminer.yaml
kubectl apply -f kubernetes/infra/rabbitmq.yaml

kubectl apply -f kubernetes/apps/io-service.yaml
kubectl rollout restart deployment io-service

kubectl apply -f kubernetes/apps/main-service.yaml
kubectl rollout restart deployment main-service

kubectl apply -f kubernetes/apps/auth-deploy.yaml
kubectl rollout restart deployment auth-service

kubectl apply -f kubernetes/apps/front-deploy.yaml
kubectl rollout restart deployment frontend-ui

kubectl apply -f kubernetes/infra/kong-gateway.yaml
kubectl rollout restart deployment kong-gateway

kubectl apply -f kubernetes/infra/portainer.yaml
kubectl rollout restart deployment portainer

kubectl apply -f kubernetes/infra/network-topology.yaml

# 9. Așteptare Pod-uri
echo "⏳ Așteptare pornire Pod-uri (poate dura 1-3 minute)..."
kubectl wait --for=condition=ready pod -l app=io-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=main-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=auth-service --timeout=300s
kubectl wait --for=condition=ready pod -l app=frontend-ui --timeout=300s
kubectl wait --for=condition=ready pod -l app=kong-gateway --timeout=300s

# 10. Port-forward pe 0.0.0.0
echo "🔌 Expunere porturi..."
kubectl port-forward --address 0.0.0.0 svc/io-service 8000:8000 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/main-service 8001:8001 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/auth-service 8002:8002 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/postgres-db 5432:5432 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/rabbitmq-service 15672:15672 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/adminer-service 8080:8080 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/kong-gateway 8443:8000 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/frontend-ui 3001:80 > /dev/null 2>&1 &
kubectl port-forward --address 0.0.0.0 svc/portainer-service 9000:9000 > /dev/null 2>&1 &

echo "⏳ Așteptare Grafana..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana --timeout=300s
kubectl port-forward --address 0.0.0.0 svc/loki-grafana 3000:80 > /dev/null 2>&1 &

GRAFANA_PASS=$(kubectl get secret loki-grafana -o jsonpath="{.data.admin-password}" | base64 --decode)

echo ""
echo "✨ SETUP FINALIZAT CU SUCCES! ✨"
echo "Verificare distribuție pe noduri:"
kubectl get pods -o wide | awk '{print $1, $7}'
echo "═══════════════════════════════════════════════════"
echo "👉 CUM ACCESEZI APLICAȚIA PE KILLERCODA:"
echo "1. În dreapta ecranului, găsește meniul 'Traffic / Ports' (sau iconița cu săgeți încrucișate)."
echo "2. Introdu portul dorit în căsuța 'Custom Port' și apasă 'Access':"
echo "   - 3001  (Frontend UI)"
echo "   - 8443  (Kong Gateway)"
echo "   - 3000  (Grafana | User: admin | Pass: $GRAFANA_PASS)"
echo "   - 8080  (Adminer)"
echo "   - 15672 (RabbitMQ | User: guest | Pass: guest)"
echo "═══════════════════════════════════════════════════"