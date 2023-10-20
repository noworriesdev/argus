#!/bin/bash
# Exit on error
set -e
# Ensure .env file exists
if [[ ! -f .env ]]; then
    echo "Error: .env file not found."
    exit 1
fi

# Declaring main variables
namespace="argus"
secrets_name="argus-secrets"

# Create namespace if it doesn't exist
./scripts/k8s/create_namespace.sh "$namespace"

echo "Initial config on Minikube..."
./scripts/k8s/minikube_setup.sh

echo "Storing secrets in Kube..."
./scripts/k8s/generate_secrets.sh "$namespace" "$secrets_name"

echo "Deploying Neo4j..."
./scripts/k8s/deploy_and_load_neo4j.sh "$namespace"



# echo "Building Airflow Docker image..."
# docker build -t argus-airflow:latest ./docker/airflow

# # Add the Apache Airflow Helm repository
# helm repo add apache-airflow https://airflow.apache.org
# helm repo update

# # Install or Upgrade Airflow using Helm
# echo "Deploying Airflow..."
# helm upgrade --install \
#     --namespace argus \
#     --create-namespace \
#     --values ./config/airflow/values.yml \
#     argus-airflow \
#     apache-airflow/airflow

# echo "Airflow should now be deploying. Monitor the pods using: kubectl get pods --namespace argus -w"