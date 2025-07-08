# Déploiement du Frontend sur Kubernetes

## Sommaire
1. Présentation
2. Prérequis
3. Fichiers fournis
4. Déploiement du frontend
5. Redéploiement du frontend
6. Accès à l'application
7. Utilisation d'un Ingress
7bis. Utilisation d'un nom de domaine personnalisé
8. Dépannage
9. FAQ

---

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

---

Pour toute question ou problème, consultez la documentation Kubernetes ou contactez l'administrateur du cluster. 