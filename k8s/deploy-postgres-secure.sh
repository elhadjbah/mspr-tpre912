#!/bin/bash

echo "Déploiement sécurisé de PostgreSQL..."

# Créer le répertoire de données sur le nœud
echo "Création du répertoire de données..."
sudo mkdir -p /mnt/data/postgres
sudo chmod 777 /mnt/data/postgres

# Appliquer les ressources Kubernetes
echo "Application des secrets PostgreSQL..."
kubectl apply -f postgres-secrets.yaml

echo "Application du script d'initialisation..."
kubectl apply -f postgres-init-configmap.yaml

echo "Application du PersistentVolume..."
kubectl apply -f postgres-pv.yaml

echo "Application du PersistentVolumeClaim..."
kubectl apply -f postgres-pvc.yaml

echo "Application du déploiement PostgreSQL..."
kubectl apply -f postgres-deployment.yaml

echo "Application du service PostgreSQL (ClusterIP)..."
kubectl apply -f postgres-service-clusterip.yaml

echo "Application de la Network Policy..."
kubectl apply -f postgres-network-policy.yaml

echo "Application du proxy pgBouncer..."
kubectl apply -f pgbouncer-configmap.yaml
kubectl apply -f postgres-proxy-deployment.yaml

# Attendre que les pods soient prêts
echo "Attente que les pods soient prêts..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
kubectl wait --for=condition=ready pod -l app=postgres-proxy --timeout=300s

echo "PostgreSQL sécurisé déployé avec succès!"
echo ""
echo "=== Configuration de sécurité appliquée ==="
echo "✅ Secrets Kubernetes pour les informations sensibles"
echo "✅ Network Policy pour restreindre l'accès réseau"
echo "✅ Service ClusterIP (accès interne uniquement)"
echo "✅ Proxy pgBouncer pour la limitation de connexions"
echo "✅ Authentification MD5"
echo "✅ TLS/SSL supporté"
echo ""
echo "=== Connexion depuis l'intérieur du cluster ==="
echo "Host: postgres-proxy"
echo "Port: 5432"
echo "Database: cofrap"
echo "Username: cofrap"
echo "Password: cofrap123"
echo ""
echo "=== Pour l'accès externe, utilisez port-forward ==="
echo "kubectl port-forward service/postgres-proxy 5432:5432"
echo ""
echo "=== Vérification de la sécurité ==="
echo "Pods en cours d'exécution:"
kubectl get pods -l app=postgres
kubectl get pods -l app=postgres-proxy
echo ""
echo "Services:"
kubectl get services -l app=postgres
echo ""
echo "Network Policies:"
kubectl get networkpolicies 