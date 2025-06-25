#!/bin/bash
set -e
NAMESPACE=cofrap
kubectl delete pod -l app=postgres -n $NAMESPACE --ignore-not-found
kubectl delete pvc -n $NAMESPACE -l app=postgres --ignore-not-found
kubectl delete pvc -n $NAMESPACE -l component=postgres --ignore-not-found
kubectl get pods -n $NAMESPACE 