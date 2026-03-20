#!/bin/bash

kubectl delete secret postgres-secrets --ignore-not-found
kubectl create secret generic postgres-secrets --from-env-file=.env

kubectl apply -f kubernetes/infra/postgres.yaml

kubectl apply -f kubernetes/apps/io-service.yaml

kubectl rollout restart deployment io-service

echo "waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=io-service --timeout=60s

kubectl port-forward svc/io-service 8000:8000 &
kubectl port-forward svc/postgres-db 5432:5432 &

echo "Services are up and running. You can access the io-service at http://localhost:8000 and the postgres database at localhost:5432."