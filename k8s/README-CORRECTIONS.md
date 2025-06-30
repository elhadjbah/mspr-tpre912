# Corrections apportées à la configuration PostgreSQL

## Problèmes identifiés et corrigés

### 1. **Incohérence StatefulSet vs PVC statique**
**Problème** : Le StatefulSet utilisait un PVC statique au lieu du volumeClaimTemplate.
**Solution** : Suppression des références au PVC statique dans les scripts de déploiement.

### 2. **Script d'initialisation incorrect**
**Problème** : Le script créait un utilisateur et une base de données alors que PostgreSQL les crée automatiquement via les variables d'environnement.
**Solution** : Simplification du script pour se contenter de créer la table `users`.

### 3. **Namespace dupliqué**
**Problème** : Deux namespaces définis dans le même fichier.
**Solution** : Conservation uniquement du namespace `cofrap`.

### 4. **Scripts de déploiement incohérents**
**Problème** : Les scripts ne géraient pas correctement les StatefulSets.
**Solution** : Correction des commandes de suppression et de déploiement.

## Fichiers modifiés

1. **postgres-init-configmap.yaml** : Script d'initialisation simplifié
2. **namespace.yaml** : Suppression du namespace dupliqué
3. **deploy-postgres.sh** : Correction de la commande de vérification
4. **redeploy-postgres.sh** : Correction des commandes de suppression
5. **verify-postgres.sh** : Nouveau script de vérification

## Utilisation

### Déploiement initial
```bash
cd k8s
./deploy-postgres.sh
```

### Redéploiement complet
```bash
cd k8s
./redeploy-postgres.sh
```

### Vérification
```bash
cd k8s
./verify-postgres.sh
```

### Connexion externe
```bash
psql -h <IP_DU_NOEUD> -p 30002 -U cofrap -d cofrap
```

## Configuration finale

- **Namespace** : cofrap
- **Base de données** : cofrap
- **Utilisateur** : cofrap
- **Mot de passe** : cofrap123
- **Port externe** : 30002
- **Type de déploiement** : StatefulSet avec volumeClaimTemplate 