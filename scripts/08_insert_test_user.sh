#!/bin/bash
set -e
NAMESPACE=cofrap
POD=$(kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n $NAMESPACE $POD -- bash -c "PGPASSWORD=secure_pass psql -U cofrap_user -d cofrap -c \"INSERT INTO users (username, password, mfa, gendate, expired) VALUES ('testuser', 'testpass', 'testmfa', NOW(), false) ON CONFLICT (username) DO NOTHING;\"" 