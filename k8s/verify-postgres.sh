#!/bin/bash

echo "=== Vérification de PostgreSQL ==="

# Vérifier l'état des pods
echo "1. État des pods:"
kubectl get pods -n cofrap

echo ""
echo "2. État des services:"
kubectl get svc -n cofrap

echo ""
echo "3. État des PVC:"
kubectl get pvc -n cofrap

echo ""
echo "4. État des PV:"
kubectl get pv

echo ""
echo "5. Vérification de la base de données:"
POD_NAME=$(kubectl get pods -l app=postgres -n cofrap -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -n "$POD_NAME" ]; then
    echo "Pod trouvé: $POD_NAME"
    
    # Vérifier que le pod est prêt
    READY=$(kubectl get pod $POD_NAME -n cofrap -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null)
    
    if [ "$READY" = "true" ]; then
        echo "Pod est prêt. Test de connexion à la base de données..."
        
        # Test de connexion
        kubectl exec $POD_NAME -n cofrap -- psql -U cofrap -d cofrap -c "SELECT version();" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅ Connexion à la base de données réussie!"
            
            # Vérifier la table users
            echo ""
            echo "6. Contenu de la table users:"
            kubectl exec $POD_NAME -n cofrap -- psql -U cofrap -d cofrap -c "SELECT * FROM users;"
        else
            echo "❌ Échec de la connexion à la base de données"
        fi
    else
        echo "❌ Pod n'est pas prêt"
    fi
else
    echo "❌ Aucun pod PostgreSQL trouvé"
fi

echo ""
echo "7. Test de connexion externe:"
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
if [ -n "$NODE_IP" ]; then
    echo "IP du nœud: $NODE_IP"
    echo "Test de connexion sur le port 30002..."
    nc -z -w5 $NODE_IP 30002
    if [ $? -eq 0 ]; then
        echo "✅ Port 30002 accessible"
        echo "Pour vous connecter: psql -h $NODE_IP -p 30002 -U cofrap -d cofrap"
    else
        echo "❌ Port 30002 non accessible"
    fi
else
    echo "❌ Impossible de récupérer l'IP du nœud"
fi 