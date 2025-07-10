# Déploiement du Frontend

## 🚦 PRÉREQUIS AVANT DÉPLOIEMENT

Avant d’exécuter les scripts `deploy-frontend.sh` ou `redeploy-frontend.sh`, il est indispensable de suivre ces étapes :

### 1. Démarrer Minikube
```bash
minikube start
```

### 2. Activer l’addon Ingress de Minikube
```bash
minikube addons enable ingress
```

### 3. Vérifier que l’Ingress Controller est bien lancé
```bash
kubectl get pods -n kube-system | grep ingress
```
- Le pod doit être en statut `Running`.
- Si ce n’est pas le cas, patiente quelques instants et relance la commande.

### 4. Ne pas utiliser `sudo` pour Minikube ou les scripts
Utilisez simplement :
```bash
./deploy-frontend.sh
# ou
./redeploy-frontend.sh
```
N’utilisez `sudo` que pour éditer le fichier `/etc/hosts` si besoin.

---

## Déploiement du frontend

(Les instructions existantes suivent ici...)

## 1. Présentation
Ce dossier contient tout le nécessaire pour déployer le frontend Dockerisé (`ghcr.io/florent228/faas-frontend:master-848f02a`) sur un cluster Kubernetes, dans le namespace `cofrap`. L'application est exposée à l'extérieur du cluster via un Service NodePort et un Ingress.

## 2. Prérequis
- Un cluster Kubernetes fonctionnel (ex : Minikube, Kind, K3s, etc.)
- `kubectl` configuré pour accéder à votre cluster
- Le namespace `cofrap` créé (`kubectl apply -f namespace.yaml` si besoin)
- Un Ingress Controller installé (ex : NGINX Ingress)

## 3. Fichiers fournis
- `frontend-deployment.yaml` : Déploiement du frontend
- `frontend-service.yaml` : Service NodePort pour exposer le frontend
- `frontend-ingress.yaml` : Ingress pour accès via nom de domaine
- `deploy-frontend.sh` : Script de déploiement automatisé
- `redeploy-frontend.sh` : Script de redéploiement complet

## 4. Déploiement du frontend

```bash
cd k8s
./deploy-frontend.sh
```
Le script applique les manifests et attend que le pod frontend soit prêt.

## 5. Redéploiement du frontend

Pour supprimer puis redéployer le frontend (utile après modification des manifests) :
```bash
cd k8s
./redeploy-frontend.sh
```

## 6. Accès à l'application

### a) Via NodePort
- Récupérez l'IP de votre node (ex : `minikube ip`)
- Accédez à : `http://<IP_NODE>:30080`

### b) Via Ingress (nom de domaine)
- Ajoutez dans votre fichier hosts (`/etc/hosts` ou `C:\Windows\System32\drivers\etc\hosts`) :
  ```
  <IP_NODE> frontend.local
  ```
- Accédez à : `http://frontend.local`

## 7. Utilisation d'un Ingress
- Le fichier `frontend-ingress.yaml` expose le service frontend sur le host `frontend.local`.
- Nécessite un Ingress Controller (ex : NGINX) installé sur le cluster.
- Modifiez le champ `host:` si vous souhaitez un autre nom de domaine.

## 7bis. Utilisation d'un nom de domaine personnalisé

Pour accéder au frontend via un nom de domaine personnalisé (ex : `monapp.mondomaine.com`), suivez ces étapes :

### a) Modifier le manifest Ingress

Dans `frontend-ingress.yaml`, changez la valeur du champ `host:` :
```yaml
spec:
  rules:
    - host: monapp.mondomaine.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
```

### b) Appliquer la modification
```bash
kubectl apply -f frontend-ingress.yaml -n cofrap
```

### c) Configurer le DNS ou le fichier hosts

- **En production** :
  - Créez un enregistrement DNS de type A pointant `monapp.mondomaine.com` vers l'IP publique de votre Ingress Controller ou de votre node.
- **En local (test)** :
  - Ajoutez dans `/etc/hosts` (Linux/Mac) ou `C:\Windows\System32\drivers\etc\hosts` (Windows) :
    ```
    <IP_NODE> monapp.mondomaine.com
    ```
  - Remplacez `<IP_NODE>` par l'IP de votre node (ex : `minikube ip`).

### d) Accéder à l'application
- Rendez-vous sur : `http://monapp.mondomaine.com`

### Points d'attention
- Le nom de domaine doit correspondre exactement à la valeur du champ `host:` dans le manifest Ingress.
- Si vous utilisez HTTPS, configurez également un certificat TLS dans l'Ingress (voir documentation de votre Ingress Controller).
- Assurez-vous que l'Ingress Controller est bien installé et fonctionne sur votre cluster.

## 7ter. Activer HTTPS avec cert-manager et Let's Encrypt

Pour sécuriser l'accès à votre frontend avec HTTPS automatiquement :

1. **Installer cert-manager** sur votre cluster (voir https://cert-manager.io/docs/)
2. **Créer un ClusterIssuer** pour Let's Encrypt (exemple dans la doc cert-manager)
3. **Modifier le manifest Ingress** comme suit :

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  namespace: cofrap
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - monapp.mondomaine.com
      secretName: frontend-tls
  rules:
    - host: monapp.mondomaine.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
```

- Le certificat sera généré et renouvelé automatiquement.
- Accédez ensuite à `https://monapp.mondomaine.com`

## 7quater. Exposer plusieurs domaines (multi-domaines)

Vous pouvez exposer le frontend sur plusieurs domaines en ajoutant plusieurs règles dans le même Ingress :

```yaml
spec:
  rules:
    - host: frontend1.mondomaine.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
    - host: frontend2.mondomaine.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
```

## 7quinquies. Forcer la redirection HTTP vers HTTPS (NGINX Ingress)

Pour forcer la redirection automatique de HTTP vers HTTPS, ajoutez l'annotation suivante dans le manifest Ingress :

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
```

## 8. Dépannage
- Vérifiez que le pod frontend est prêt :
  ```bash
  kubectl get pods -n cofrap
  ```
- Vérifiez les logs du pod :
  ```bash
  kubectl logs <nom-du-pod> -n cofrap
  ```
- Vérifiez que le service est bien exposé :
  ```bash
  kubectl get svc -n cofrap
  ```
- Vérifiez l'Ingress :
  ```bash
  kubectl get ingress -n cofrap
  ```

## 9. FAQ

**Q : Comment changer l'image Docker du frontend ?**
> Modifiez la ligne `image:` dans `frontend-deployment.yaml` puis relancez le déploiement.

**Q : Comment changer le port d'accès externe ?**
> Modifiez la valeur `nodePort:` dans `frontend-service.yaml` (ex : 30080).

**Q : Comment utiliser un autre nom de domaine ?**
> Modifiez le champ `host:` dans `frontend-ingress.yaml` et dans votre fichier hosts.

**Q : Comment supprimer complètement le frontend ?**
> Utilisez :
> ```bash
> kubectl delete deployment frontend -n cofrap
> kubectl delete service frontend-service -n cofrap
> kubectl delete ingress frontend-ingress -n cofrap
> ```

**Q : Comment déboguer un problème d'Ingress qui ne fonctionne pas ?**
> - Vérifiez que l'Ingress Controller est bien déployé (`kubectl get pods -n ingress-nginx` ou namespace équivalent).
> - Vérifiez les logs du contrôleur (`kubectl logs <pod-ingress-controller> -n ingress-nginx`).
> - Vérifiez que le DNS ou le fichier hosts pointe bien vers l'IP du contrôleur.
> - Vérifiez que le port 80 (et 443 si HTTPS) est ouvert sur le node.
> - Vérifiez la syntaxe de votre manifest Ingress et la correspondance exacte du champ `host:`.

---

Pour toute question ou problème, consultez la documentation Kubernetes ou contactez l'administrateur du cluster. 