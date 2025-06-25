#!/bin/bash
kubectl create namespace openfaas
kubectl create namespace openfaas-fn
helm repo add openfaas https://openfaas.github.io/faas-netes/
helm repo update
helm upgrade openfaas --install openfaas/openfaas \
  --namespace openfaas \
  --set basic_auth=true \
  --set gateway.directFunctions=true \
  --set gateway.service.type=ClusterIP \
  --set faasnetes.imagePullPolicy=IfNotPresent 