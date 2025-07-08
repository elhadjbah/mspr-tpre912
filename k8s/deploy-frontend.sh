#!/bin/bash

echo "Déploiement du frontend..."

kubectl apply -f frontend-deployment.yaml -n cofrap
kubectl apply -f frontend-service.yaml -n cofrap
kubectl apply -f frontend-ingress.yaml -n cofrap

# Attendre que le pod frontend soit prêt
echo "Attente que le pod frontend soit prêt..."
kubectl wait --for=condition=ready pod -l app=frontend --timeout=180s -n cofrap

echo "Frontend déployé avec succès !" 