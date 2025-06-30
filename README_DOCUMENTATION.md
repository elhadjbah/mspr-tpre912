# Documentation Complète - Déploiement PostgreSQL sur Kubernetes

## Table des matières

1. [Architecture générale](#architecture-générale)
2. [Namespace et isolation](#namespace-et-isolation)
3. [Gestion des secrets](#gestion-des-secrets)
4. [Configuration PostgreSQL](#configuration-postgresql)
5. [Stockage persistant](#stockage-persistant)
6. [Services et exposition](#services-et-exposition)
7. [Scripts de déploiement](#scripts-de-déploiement)
8. [Scripts de diagnostic](#scripts-de-diagnostic)
9. [Choix architecturaux](#choix-architecturaux)
10. [Sécurité](#sécurité)
11. [Maintenance et opérations](#maintenance-et-opérations)

---

## Architecture générale

### Vue d'ensemble
Le projet implémente une base de données PostgreSQL déployée sur Kubernetes avec les caractéristiques suivantes :
- **Isolation** : Namespace dédié `cofrap`
- **Persistance** : Stockage persistant via StatefulSet
- **Sécurité** : Secrets Kubernetes pour les credentials
- **Exposition** : Service NodePort pour accès externe
- **Initialisation** : Script automatique de création de tables

### Composants principaux
1. **StatefulSet** : Gestion du pod PostgreSQL avec identité stable
2. **PersistentVolume** : Stockage local sur le nœud
3. **Service NodePort** : Exposition sur le port 30002
4. **ConfigMap** : Script d'initialisation de la base
5. **Secret** : Credentials de la base de données

---

## Namespace et isolation

### Fichier : `k8s/namespace.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cofrap
```

**Choix architectural :**
- **Isolation complète** : Le namespace `cofrap` isole toutes les ressources PostgreSQL
- **Gestion des ressources** : Permet l'application de quotas et limites
- **Sécurité** : Évite les conflits avec d'autres applications
- **Organisation** : Facilite la gestion et le monitoring

**Pourquoi ce choix :**
- **Séparation des préoccupations** : Chaque application a son propre espace
- **Facilité de maintenance** : Suppression facile de toutes les ressources
- **Sécurité renforcée** : Isolation réseau et des ressources
- **Évolutivité** : Possibilité d'ajouter d'autres services dans le même namespace

---

## Gestion des secrets

### Fichier : `k8s/postgres-secrets.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secrets
  namespace: cofrap
  labels:
    app: postgres
type: Opaque
data:
  username: Y29mcmFw        # cofrap en base64
  password: Y29mcmFwMTIz    # cofrap123 en base64
  database: Y29mcmFw        # cofrap en base64
```

**Choix techniques :**

1. **Encodage Base64** :
   - **Pourquoi** : Kubernetes exige l'encodage Base64 pour les secrets
   - **Sécurité** : N'est pas du chiffrement, mais évite l'affichage en clair
   - **Limitation** : Doit être combiné avec RBAC pour une vraie sécurité

2. **Structure des données** :
   - **username** : Utilisateur PostgreSQL
   - **password** : Mot de passe de l'utilisateur
   - **database** : Nom de la base de données

3. **Nommage** :
   - **postgres-secrets** : Nom explicite indiquant le contenu
   - **Namespace cofrap** : Isolation des secrets

**Avantages de cette approche :**
- **Séparation des credentials** du code applicatif
- **Gestion centralisée** des secrets
- **Rotation facile** des mots de passe
- **Intégration native** avec les variables d'environnement

---

## Configuration PostgreSQL

### Fichier : `k8s/postgres-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: cofrap
spec:
  selector:
    matchLabels:
      app: postgres
  serviceName: "postgres-service"
  replicas: 1
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - image: postgres:15
        name: postgres
        env:
          - name: POSTGRES_DB
            valueFrom:
              secretKeyRef:
                name: postgres-secrets
                key: database
          - name: POSTGRES_USER
            valueFrom:
              secretKeyRef:
                name: postgres-secrets
                key: username
          - name: POSTGRES_PASSWORD
            valueFrom:
              secretKeyRef:
                name: postgres-secrets
                key: password
        ports:
        - containerPort: 5432
          name: postgres
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: postgres-init-script
          mountPath: /docker-entrypoint-initdb.d
      volumes:
      - name: postgres-init-script
        configMap:
          name: postgres-init-script
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 1Gi
```

**Choix architecturaux critiques :**

1. **StatefulSet vs Deployment** :
   - **Pourquoi StatefulSet** : 
     - Identité stable du pod (`postgres-0`)
     - Stockage persistant dédié
     - Ordre de démarrage garanti
     - Nom DNS stable
   - **Avantages** : Idéal pour les bases de données avec état

2. **Variables d'environnement PostgreSQL** :
   - **POSTGRES_DB** : Crée automatiquement la base de données
   - **POSTGRES_USER** : Crée automatiquement l'utilisateur
   - **POSTGRES_PASSWORD** : Définit le mot de passe
   - **Avantage** : Initialisation automatique sans scripts complexes

3. **VolumeClaimTemplate** :
   - **Pourquoi** : Chaque pod StatefulSet a son propre PVC
   - **Nommage automatique** : `postgres-storage-postgres-0`
   - **Persistance** : Survit aux redémarrages du pod

4. **Image PostgreSQL 15** :
   - **Version LTS** : Support long terme
   - **Stabilité** : Version éprouvée en production
   - **Fonctionnalités** : Support des dernières fonctionnalités

---

## Script d'initialisation

### Fichier : `k8s/postgres-init-configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-init-script
  namespace: cofrap
data:
  init.sql: |
    -- La base de données et l'utilisateur sont créés automatiquement par les variables d'environnement
    -- POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    
    -- Se connecter à la base de données créée automatiquement
    \connect cofrap;

    -- Créer la table users
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        mfa VARCHAR(255) NOT NULL,
        gendate TIMESTAMP NOT NULL,
        expired BOOLEAN NOT NULL DEFAULT FALSE
    );

    -- Insérer un utilisateur de test
    INSERT INTO users (username, password, mfa, gendate, expired)
    VALUES ('admin', 'admin_pass', 'off', NOW(), false)
    ON CONFLICT (username) DO NOTHING;
```

**Choix de conception :**

1. **Utilisation des variables d'environnement** :
   - **Pourquoi** : PostgreSQL crée automatiquement la DB et l'utilisateur
   - **Simplicité** : Évite les scripts complexes de création
   - **Fiabilité** : Moins d'erreurs potentielles

2. **Structure de la table users** :
   - **id** : Clé primaire auto-incrémentée
   - **username** : Unique, pour éviter les doublons
   - **password** : Stockage du hash du mot de passe
   - **mfa** : Support de l'authentification multi-facteurs
   - **gendate** : Horodatage de création
   - **expired** : Gestion de l'expiration des comptes

3. **ON CONFLICT DO NOTHING** :
   - **Idempotence** : Le script peut être exécuté plusieurs fois
   - **Sécurité** : Évite les erreurs de duplication

4. **Montage dans `/docker-entrypoint-initdb.d`** :
   - **Standard PostgreSQL** : Répertoire reconnu par l'image officielle
   - **Exécution automatique** : Scripts exécutés au premier démarrage

---

## Stockage persistant

### Fichier : `k8s/postgres-pv.yaml`

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: postgres-pv
  namespace: cofrap
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/mnt/data/postgres"
```

**Choix de stockage :**

1. **hostPath** :
   - **Pourquoi** : Stockage local sur le nœud
   - **Simplicité** : Pas de configuration complexe
   - **Performance** : Accès direct au système de fichiers
   - **Limitation** : Tiedé au nœud spécifique

2. **ReadWriteOnce** :
   - **Pourquoi** : Un seul pod peut monter le volume
   - **Cohérence** : Évite les conflits d'accès
   - **Sécurité** : Isolation des données

3. **1Gi de stockage** :
   - **Taille raisonnable** : Suffisant pour les données de test
   - **Évolutivité** : Peut être augmenté selon les besoins

**Note importante** : Avec le StatefulSet, ce PV n'est plus utilisé directement. Le StatefulSet crée son propre PVC via le volumeClaimTemplate.

---

## Services et exposition

### Fichier : `k8s/postgres-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: cofrap
spec:
  type: NodePort
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
    nodePort: 30002
    name: postgres
```

**Choix de service :**

1. **NodePort** :
   - **Pourquoi** : Exposition externe au cluster
   - **Simplicité** : Pas de LoadBalancer externe nécessaire
   - **Port fixe** : 30002 pour accès prévisible
   - **Limitation** : Expose sur tous les nœuds

2. **Port mapping** :
   - **port: 5432** : Port interne du service
   - **targetPort: 5432** : Port du conteneur PostgreSQL
   - **nodePort: 30002** : Port externe sur le nœud

3. **Selector app: postgres** :
   - **Ciblage** : Route le trafic vers les pods avec ce label
   - **Flexibilité** : Fonctionne avec StatefulSet et Deployment

**Alternatives considérées :**
- **ClusterIP** : Accès interne uniquement
- **LoadBalancer** : Exposition externe avec IP dédiée
- **Ingress** : Exposition via reverse proxy

---

## Scripts de déploiement

### Fichier : `k8s/deploy-postgres.sh`

```bash
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

# ... vérifications et affichage des informations
```

**Choix de conception :**

1. **Ordre d'application** :
   - **Namespace en premier** : Création de l'environnement
   - **Secrets et ConfigMaps** : Ressources nécessaires aux pods
   - **Volumes** : Stockage avant les pods
   - **Service** : Exposition avant les pods
   - **StatefulSet** : Application principale

2. **Création du répertoire** :
   - **sudo mkdir** : Création avec privilèges
   - **chmod 777** : Permissions larges pour les tests
   - **Note** : En production, utiliser des permissions plus restrictives

3. **Attente du pod** :
   - **kubectl wait** : Attente conditionnelle
   - **timeout=300s** : 5 minutes maximum
   - **Évite** : Les erreurs de timing

4. **Gestion robuste des pods** :
   - **Nom correct** : `postgres-0` pour StatefulSet
   - **Vérification d'état** : Pod prêt avant connexion
   - **Fallback** : Recherche alternative si pod non trouvé

---

### Fichier : `k8s/redeploy-postgres.sh`

```bash
#!/bin/bash

echo "Redéploiement de PostgreSQL avec réinitialisation..."

# Supprimer l'ancien déploiement
echo "Suppression de l'ancien déploiement..."
kubectl delete statefulset postgres -n cofrap --ignore-not-found=true
kubectl delete service postgres-service -n cofrap --ignore-not-found=true
kubectl delete pvc postgres-storage-postgres-0 -n cofrap --ignore-not-found=true
kubectl delete pv postgres-pv --ignore-not-found=true
kubectl delete configmap postgres-init-script -n cofrap --ignore-not-found=true
kubectl delete secret postgres-secrets -n cofrap --ignore-not-found=true

# ... nettoyage et redéploiement
```

**Choix de nettoyage :**

1. **--ignore-not-found=true** :
   - **Pourquoi** : Évite les erreurs si la ressource n'existe pas
   - **Idempotence** : Le script peut être exécuté plusieurs fois

2. **Ordre de suppression** :
   - **StatefulSet en premier** : Libère les PVC
   - **Service** : Arrête l'exposition
   - **PVC** : Libère les volumes
   - **PV** : Libère le stockage
   - **ConfigMaps/Secrets** : Ressources de configuration

3. **Nettoyage du répertoire** :
   - **rm -rf** : Suppression complète des données
   - **Réinitialisation** : Base de données propre

---

## Scripts de diagnostic

### Fichier : `k8s/verify-postgres.sh`

Script de vérification rapide avec tests automatisés.

**Fonctionnalités :**
- Vérification de l'état des pods
- Test de connexion à PostgreSQL
- Vérification des tables
- Test de connectivité externe

### Fichier : `k8s/check-postgres.sh`

Script de diagnostic détaillé avec logs et informations complètes.

**Fonctionnalités :**
- État détaillé de tous les composants
- Affichage des logs du pod
- Test de connexion à la base
- Vérification des données
- Diagnostic réseau

---

## Choix architecturaux

### 1. **StatefulSet vs Deployment**

**Choix : StatefulSet**

**Pourquoi :**
- **Identité stable** : Le pod garde toujours le nom `postgres-0`
- **Stockage dédié** : Chaque pod a son propre volume persistant
- **Ordre de démarrage** : Garantit l'ordre dans un cluster multi-pods
- **Nom DNS stable** : `postgres-0.postgres-service.cofrap.svc.cluster.local`

**Alternatives rejetées :**
- **Deployment** : Pas d'identité stable, volumes partagés
- **DaemonSet** : Un pod par nœud, surkill pour notre cas

### 2. **Stockage : hostPath vs autres solutions**

**Choix : hostPath**

**Pourquoi :**
- **Simplicité** : Pas de configuration complexe
- **Performance** : Accès direct au système de fichiers
- **Compatibilité** : Fonctionne sur tous les clusters

**Alternatives considérées :**
- **NFS** : Complexité de configuration
- **Cloud Storage** : Dépendance externe
- **Local Storage** : Spécifique à certains clusters

### 3. **Service : NodePort vs autres types**

**Choix : NodePort**

**Pourquoi :**
- **Exposition externe** : Accès depuis l'extérieur du cluster
- **Simplicité** : Pas de LoadBalancer externe nécessaire
- **Port fixe** : 30002 pour accès prévisible

**Alternatives rejetées :**
- **ClusterIP** : Accès interne uniquement
- **LoadBalancer** : Coût et complexité supplémentaires
- **Ingress** : Overkill pour une base de données

### 4. **Gestion des secrets**

**Choix : Secrets Kubernetes**

**Pourquoi :**
- **Intégration native** : Avec les variables d'environnement
- **Gestion centralisée** : Un seul endroit pour les credentials
- **Séparation** : Des credentials du code

**Alternatives rejetées :**
- **Variables d'environnement en dur** : Insécurité
- **External Secret Manager** : Complexité supplémentaire
- **HashiCorp Vault** : Overkill pour ce projet

---

## Sécurité

### 1. **Isolation par namespace**
- **Isolation réseau** : Ressources isolées
- **RBAC** : Contrôle d'accès granulaire possible
- **Quotas** : Limitation des ressources

### 2. **Gestion des secrets**
- **Encodage Base64** : Masquage des valeurs
- **Namespace isolé** : Secrets dans le namespace cofrap
- **Intégration native** : Avec les variables d'environnement

### 3. **Limitations actuelles**
- **hostPath** : Accès direct au système de fichiers
- **Permissions 777** : Trop permissives pour la production
- **Pas de chiffrement** : Des secrets en transit

### 4. **Améliorations recommandées**
- **RBAC** : Contrôle d'accès aux secrets
- **Network Policies** : Isolation réseau renforcée
- **Chiffrement** : Des secrets au repos
- **Audit** : Logs d'accès aux secrets

---

## Maintenance et opérations

### 1. **Backup et restauration**
- **Sauvegarde** : Du répertoire `/mnt/data/postgres`
- **Restauration** : Remplacement du répertoire
- **Scripts** : Automatisation possible

### 2. **Monitoring**
- **Logs** : `kubectl logs postgres-0 -n cofrap`
- **Métriques** : Prometheus/Grafana possible
- **Santé** : Scripts de vérification

### 3. **Mise à jour**
- **Image** : Changement de version PostgreSQL
- **Configuration** : Modification des ConfigMaps
- **Rolling update** : Mise à jour sans interruption

### 4. **Scaling**
- **Horizontal** : Ajout de réplicas (attention aux données)
- **Vertical** : Augmentation des ressources
- **Stockage** : Augmentation de la taille des volumes

---

## Conclusion

Cette architecture PostgreSQL sur Kubernetes offre :

**Avantages :**
- **Haute disponibilité** : Gestion automatique des pods
- **Persistance** : Données préservées lors des redémarrages
- **Scalabilité** : Possibilité d'ajouter des réplicas
- **Maintenabilité** : Scripts automatisés
- **Sécurité** : Isolation et gestion des secrets

**Limitations :**
- **Complexité** : Plus complexe qu'une installation directe
- **Dépendances** : Nécessite un cluster Kubernetes
- **Performance** : Overhead de la virtualisation
- **Stockage** : Tiedé au nœud avec hostPath

**Utilisation recommandée :**
- **Environnements de développement** : Tests et développement
- **Petites productions** : Applications avec charge modérée
- **Apprentissage** : Compréhension de Kubernetes

Cette documentation fournit une base solide pour comprendre, maintenir et évoluer l'infrastructure PostgreSQL sur Kubernetes. 