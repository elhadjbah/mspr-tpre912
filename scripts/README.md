# Scripts d'automatisation MSPR COFRAP

1. Démarrer Minikube :
   ```bash
   ./01_start_minikube.sh
   ```
2. Installer Helm :
   ```bash
   ./02_install_helm.sh
   ```
3. Déployer OpenFaaS :
   ```bash
   ./03_deploy_openfaas.sh
   ```
4. Appliquer les manifests :
   ```bash
   ./04_apply_manifests.sh
   ```
5. Déployer les fonctions :
   ```bash
   ./05_deploy_functions.sh
   ```
6. Réinitialiser PostgreSQL (supprime le pod et le PVC, attention : perte de données) :
   ```bash
   ./06_reset_postgres.sh
   ```
7. Vérifier la table users dans PostgreSQL :
   ```bash
   ./07_check_postgres_table.sh
   ```
8. Insérer un utilisateur de test :
   ```bash
   ./08_insert_test_user.sh
   ```
9. Lire tous les utilisateurs :
   ```bash
   ./09_select_users.sh
   ```
10. Tester la fonction OpenFaaS generate_password et vérifier l'insertion en base :
   ```bash
   ./10_test_generate_password.sh
   ```

**N'oublie pas d'adapter le nom Docker Hub dans 05_deploy_functions.sh !** 