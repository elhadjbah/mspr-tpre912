#!/bin/bash

echo "Déploiement de PostgreSQL..."

# Créer le répertoire de données sur le nœud
echo "Création du répertoire de données..."
sudo mkdir -p /mnt/data/postgres
sudo chmod 777 /mnt/data/postgres

# Appliquer les ressources Kubernetes
echo "Application des secrets PostgreSQL..."
kubectl apply -f namespace.yaml
kubectl apply -f postgres-secrets.yaml -n cofrap
kubectl apply -f postgres-init-configmap.yaml -n cofrap
kubectl apply -f postgres-pv.yaml -n cofrap
kubectl apply -f postgres-pvc.yaml -n cofrap
kubectl apply -f postgres-service.yaml -n cofrap
kubectl apply -f postgres-deployment.yaml -n cofrap

# Attendre que le pod soit prêt
echo "Attente que le pod PostgreSQL soit prêt..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

echo "PostgreSQL déployé avec succès!"
echo "La table 'users' a été créée automatiquement lors de l'initialisation."
echo ""
echo "Pour vous connecter depuis l'extérieur:"
echo "Host: <IP_DU_NOEUD>"
echo "Port: 30002"
echo "Database: cofrap"
echo "Username: cofrap"
echo "Password: cofrap123"

# Afficher l'IP du nœud
echo "IP du nœud:"
kubectl get nodes -o wide

# Vérifier que la table a été créée
echo ""
echo "Vérification de la table users:"
POD_NAME=$(kubectl get pods -l app=postgres -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD_NAME -n cofrap -- psql -U cofrap -d cofrap -c "SELECT * FROM users;" 