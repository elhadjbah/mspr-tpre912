#!/bin/bash
# Variables à adapter
DOCKERHUB_USER="<dockerhub_username>"
FERNET_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

cd ../openfaas/functions
# Remplacer les placeholders dans stack.yml
sed -i "s|<dockerhub_username>|$DOCKERHUB_USER|g" stack.yml
sed -i "s|<clé_fernet_base64>|$FERNET_KEY|g" stack.yml

faas-cli build -f stack.yml
faas-cli push -f stack.yml
faas-cli deploy -f stack.yml 