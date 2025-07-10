#!/bin/bash

set -e

# Couleurs pour l'affichage
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

HOST="cofrap.local"
NAMESPACE="cofrap"
INGRESS_NAME="frontend-ingress"

# Séparateur visuel
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}Re-déploiement du frontend...${NC}"
echo -e "${CYAN}========================================${NC}"

# Suppression des ressources existantes
echo -e "${YELLOW}Suppression des ressources existantes...${NC}"
kubectl delete -f frontend-deployment.yaml -n $NAMESPACE --ignore-not-found
kubectl delete -f frontend-service.yaml -n $NAMESPACE --ignore-not-found
kubectl delete -f frontend-ingress.yaml -n $NAMESPACE --ignore-not-found

echo -e "${GREEN}Ressources supprimées (si elles existaient).${NC}"

# Déploiement des ressources frontend
echo -e "${YELLOW}Application des manifests Kubernetes...${NC}"
kubectl apply -f frontend-deployment.yaml -n $NAMESPACE
kubectl apply -f frontend-service.yaml -n $NAMESPACE
kubectl apply -f frontend-ingress.yaml -n $NAMESPACE

echo -e "${GREEN}Manifests appliqués avec succès.${NC}"

# Attendre que le pod frontend soit prêt
echo -e "${YELLOW}Attente que le pod frontend soit prêt...${NC}"
kubectl wait --for=condition=ready pod -l app=frontend --timeout=180s -n $NAMESPACE

echo -e "${GREEN}Frontend re-déployé avec succès !${NC}"
echo -e "${CYAN}========================================${NC}"

# Vérification de l'Ingress
echo -e "${YELLOW}Vérification de l'Ingress :${NC}"
echo -e "${CYAN}Commande utile : kubectl get ingress -n $NAMESPACE${NC}"
kubectl get ingress -n $NAMESPACE

echo -e "${CYAN}----------------------------------------${NC}"

# Récupérer l'IP de l'Ingress
ingress_ip=$(kubectl get ingress $INGRESS_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$ingress_ip" ]; then
  ingress_ip=$(kubectl get ingress $INGRESS_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

if [ -z "$ingress_ip" ]; then
  echo -e "${RED}Impossible de récupérer l'IP de l'Ingress.\nVérifiez que l'Ingress Controller est bien déployé et que l'Ingress est prêt.\nVous pouvez surveiller l'état avec : kubectl describe ingress $INGRESS_NAME -n $NAMESPACE${NC}"
else
  echo -e "${GREEN}Accès frontend disponible via l'Ingress !${NC}"
  echo -e "${CYAN}----------------------------------------${NC}"
  echo -e "${YELLOW}Host configuré :${NC}   ${CYAN}$HOST${NC}"
  echo -e "${YELLOW}IP de l'Ingress :${NC} ${CYAN}$ingress_ip${NC}"
  echo -e "${YELLOW}URL d'accès :${NC}     ${GREEN}http://$HOST${NC}"
  echo -e "${CYAN}----------------------------------------${NC}"
  echo -e "${YELLOW}Pour accéder au frontend, ajoutez la ligne suivante à votre fichier hosts :${NC}"
  echo -e "${CYAN}$ingress_ip   $HOST${NC}"
  echo -e "\n${YELLOW}Instructions :${NC}"
  echo -e "- Sous Linux/WSL2 : sudo nano /etc/hosts"
  echo -e "- Sous Windows   : Notepad en admin -> C:\\Windows\\System32\\drivers\\etc\\hosts"
  echo -e "${CYAN}----------------------------------------${NC}"
fi

echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}Re-déploiement terminé. Vous pouvez maintenant accéder à votre frontend !${NC}"
echo -e "${CYAN}========================================${NC}" 