#!/bin/bash

# Exit on error
set -e

# Ensure .env file exists
if [[ ! -f ./.env ]]; then
    echo ".env file not found." >&2
    exit 1
fi

# Declaring main variables
namespace="argus"
secrets_name="argus-secrets"
directory_path="/mnt/c/development/argus"  # Modify this path accordingly

# Create namespace if it doesn't exist
./scripts/linux/k8s/create_namespace.sh $namespace

echo "Initial config on Minikube..."
./scripts/linux/k8s/minikube_setup.sh $directory_path

echo "Storing secrets in Kube..."
./scripts/linux/k8s/generate_secrets.sh $namespace $secrets_name

echo "Deploying Neo4j..."
./scripts/linux/k8s/deploy_neo4j.sh $namespace $directory_path
