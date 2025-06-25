# MSPR COFRAP - Déploiement Serverless avec OpenFaaS & Kubernetes

## Fonctionnalités
- Génération de mot de passe sécurisé + QR code + stockage chiffré
- Génération de secret TOTP (2FA) + QR code + stockage chiffré
- Authentification utilisateur (login, mot de passe, 2FA, gestion expiration)

## Arborescence
- `k8s/` : Manifests Kubernetes (PostgreSQL, Ingress, etc.)
- `openfaas/functions/` : Fonctions Python OpenFaaS
- `scripts/` : Scripts d'automatisation

## Déploiement rapide
1. Démarrer Minikube :
   ```bash
   ./scripts/01_start_minikube.sh
   ```
2. Installer Helm :
   ```bash
   ./scripts/02_install_helm.sh
   ```
3. Déployer OpenFaaS :
   ```bash
   ./scripts/03_deploy_openfaas.sh
   ```
4. Appliquer les manifests :
   ```bash
   ./scripts/04_apply_manifests.sh
   ```
5. Déployer les fonctions :
   ```bash
   ./scripts/05_deploy_functions.sh
   ```

## Configuration OpenFaaS CLI
- Installer : https://docs.openfaas.com/cli/install/
- Login :
  ```bash
  PASSWORD=$(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)
  echo $PASSWORD | faas-cli login -g http://127.0.0.1:8080 -u admin --password-stdin
  ```

## Build & Push Docker Hub
- Adapter le nom Docker Hub dans `05_deploy_functions.sh` et `stack.yml`
- Les images sont buildées et poussées automatiquement par le script

## Sécurité
- Les credentials sont stockés dans des secrets Kubernetes
- Les mots de passe et secrets TOTP sont chiffrés avec Fernet

## Accès OpenFaaS
- Ingress : http://openfaas.local (ajouter dans /etc/hosts : `127.0.0.1 openfaas.local`)

## Table PostgreSQL
```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    mfa VARCHAR(255) NOT NULL,
    gendate TIMESTAMP NOT NULL,
    expired BOOLEAN NOT NULL DEFAULT FALSE
);
```

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
