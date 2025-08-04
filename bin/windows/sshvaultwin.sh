#!/usr/bin/env bash

#setx VAULT_SKIP_VERIFY true
#setx VAULT_URL https://mi-crypt-east.vault.cloud.marriott.com
setx VAULT_ADDR https://mi-crypt-east.vault.cloud.marriott.com
#setx VAULT_LDAP_MOUNT_PATH marriott
#setx SSH_CLIENT_SIGNER_PATH marriott/ssh-client-signer/sign/nwdevops-ssh
#setx TOKEN_ROLE nwdevops-ssh
#setx PRINCIPAL svc-nwdevops-adm
VAULT_TOKEN=$(vault login -method=ldap -path=marriott -token-only username="$EID" password="$PASSWORD")
#cd ~/git/vault-client-scripts
#./ssh-with-cert.sh $1
