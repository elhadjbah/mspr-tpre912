#!/bin/bash
set -e
USERNAME="testopenfaas"
# Appel de la fonction generate_password via faas-cli
RESPONSE=$(echo "{\"username\": \"$USERNAME\"}" | faas-cli invoke generate_password)
echo "Réponse de la fonction : $RESPONSE"
# Vérification en base
NAMESPACE=cofrap
POD=$(kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n $NAMESPACE $POD -- bash -c "PGPASSWORD=secure_pass psql -U cofrap_user -d cofrap -c \"SELECT username, gendate, expired FROM users WHERE username = '$USERNAME';\"" 