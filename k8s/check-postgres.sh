#!/bin/bash

echo "=== Diagnostic PostgreSQL ==="

echo "1. État des pods:"
kubectl get pods -n cofrap

echo ""
echo "2. État des StatefulSets:"
kubectl get statefulset -n cofrap

echo ""
echo "3. État des services:"
kubectl get svc -n cofrap

echo ""
echo "4. État des PVC:"
kubectl get pvc -n cofrap

echo ""
echo "5. Recherche du pod PostgreSQL:"
POD_NAME=$(kubectl get pods -l app=postgres -n cofrap -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -n "$POD_NAME" ]; then
    echo "Pod trouvé: $POD_NAME"
    echo "État du pod:"
    kubectl get pod $POD_NAME -n cofrap -o wide
    
    echo ""
    echo "Logs du pod:"
    kubectl logs $POD_NAME -n cofrap --tail=20
    
    echo ""
    echo "Test de connexion à PostgreSQL:"
    kubectl exec $POD_NAME -n cofrap -- psql -U cofrap -d cofrap -c "SELECT version();" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ PostgreSQL répond correctement"
        echo ""
        echo "Liste des bases de données:"
        kubectl exec $POD_NAME -n cofrap -- psql -U cofrap -d cofrap -c "\l" 2>/dev/null
        
        echo ""
        echo "Tables dans la base cofrap:"
        kubectl exec $POD_NAME -n cofrap -- psql -U cofrap -d cofrap -c "\dt" 2>/dev/null
        
        echo ""
        echo "Contenu de la table users:"
        kubectl exec $POD_NAME -n cofrap -- psql -U cofrap -d cofrap -c "SELECT * FROM users;" 2>/dev/null
    else
        echo "❌ Erreur de connexion à PostgreSQL"
    fi
else
    echo "❌ Aucun pod PostgreSQL trouvé"
fi

echo ""
echo "6. Test de connexion externe:"
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
if [ -n "$NODE_IP" ]; then
    echo "IP du nœud: $NODE_IP"
    echo "Test du port 30002:"
    nc -z -w5 $NODE_IP 30002 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Port 30002 accessible"
        echo "Commande de connexion: psql -h $NODE_IP -p 30002 -U cofrap -d cofrap"
    else
        echo "❌ Port 30002 non accessible"
    fi
else
    echo "❌ Impossible de récupérer l'IP du nœud"
fi 