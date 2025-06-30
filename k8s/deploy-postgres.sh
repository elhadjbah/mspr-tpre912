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
# Attendre un peu pour que PostgreSQL soit complètement initialisé
sleep 10

# Utiliser le nom de pod StatefulSet
POD_NAME="postgres-0"
if kubectl get pod $POD_NAME -n cofrap >/dev/null 2>&1; then
    echo "Pod trouvé: $POD_NAME"
    # Vérifier que le pod est prêt
    READY=$(kubectl get pod $POD_NAME -n cofrap -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null)
    if [ "$READY" = "true" ]; then
        echo "Pod est prêt. Test de connexion à la base de données..."
        kubectl exec $POD_NAME -n cofrap -- psql -U cofrap -d cofrap -c "SELECT * FROM users;" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ Vérification de la table users réussie!"
        else
            echo "⚠️  La table users n'est pas encore disponible ou erreur de connexion"
        fi
    else
        echo "⚠️  Pod n'est pas encore prêt"
    fi
else
    echo "⚠️  Pod $POD_NAME non trouvé, recherche d'un autre pod..."
    # Fallback: chercher n'importe quel pod avec le label app=postgres
    POD_NAME=$(kubectl get pods -l app=postgres -n cofrap -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$POD_NAME" ]; then
        echo "Pod trouvé: $POD_NAME"
        kubectl exec $POD_NAME -n cofrap -- psql -U cofrap -d cofrap -c "SELECT * FROM users;" 2>/dev/null
    else
        echo "❌ Aucun pod PostgreSQL trouvé"
    fi
fi 