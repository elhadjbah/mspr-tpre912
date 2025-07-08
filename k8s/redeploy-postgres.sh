#!/bin/bash

echo "Redéploiement de PostgreSQL avec réinitialisation..."

# Supprimer l'ancien déploiement
echo "Suppression de l'ancien déploiement..."
kubectl delete statefulset postgres -n cofrap --ignore-not-found=true
kubectl delete service postgres-service -n cofrap --ignore-not-found=true
kubectl delete pvc postgres-storage-postgres-0 -n cofrap --ignore-not-found=true
kubectl delete pv postgres-pv --ignore-not-found=true
kubectl delete configmap postgres-init-script -n cofrap --ignore-not-found=true
kubectl delete secret postgres-secrets -n cofrap --ignore-not-found=true
kubectl delete deployment frontend -n cofrap --ignore-not-found=true
kubectl delete service frontend-service -n cofrap --ignore-not-found=true
kubectl delete ingress frontend-ingress -n cofrap --ignore-not-found=true

# Attendre que tout soit supprimé
echo "Attente de la suppression..."
sleep 10

# Recréer le répertoire de données (vide)
echo "Nettoyage du répertoire de données..."
sudo rm -rf /mnt/data/postgres/*
sudo mkdir -p /mnt/data/postgres
sudo chmod 777 /mnt/data/postgres

# Redéployer
echo "Redéploiement..."
./deploy-postgres.sh

echo "Redéploiement terminé avec succès!" 