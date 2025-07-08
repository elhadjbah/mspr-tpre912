#!/bin/bash

echo "Suppression de l'ancien frontend..."
kubectl delete deployment frontend -n cofrap --ignore-not-found=true
kubectl delete service frontend-service -n cofrap --ignore-not-found=true
kubectl delete ingress frontend-ingress -n cofrap --ignore-not-found=true

# Attendre la suppression complète
echo "Attente de la suppression..."
sleep 5

# Redéployer le frontend
./deploy-frontend.sh

echo "Redéploiement du frontend terminé !" 