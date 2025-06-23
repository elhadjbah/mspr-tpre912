# MSPR TPRE912 – Projet Serverless sécurisé avec Kubernetes & OpenFaaS

## 🎯 Objectif
Développement d’un PoC de création/authentification d’utilisateur sécurisé, déployé sur Kubernetes via OpenFaaS.

## ⚙️ Stack technique
- Kubernetes (Minikube)
- OpenFaaS Community
- PostgreSQL (StatefulSet)
- Fonctions Python
- Frontend HTML/JS
- CI/CD GitHub Actions

## 🔐 Fonctionnalités de sécurité
- Mots de passe complexes et chiffrés
- QR Code 2FA (TOTP)
- Stockage sécurisé (Secrets K8s)
- Isolation réseau (NetworkPolicy)
- Accès limité via Ingress + auth basic
- Observabilité Prometheus

## 🧱 Structure du projet
```bash
.
├── manifests/        # YAML K8s
├── functions/        # Fonctions OpenFaaS
├── frontend/         # Interface utilisateur
├── .github/          # Workflows CI
└── README.md         # Présentation
