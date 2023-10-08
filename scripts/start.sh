#!/bin/bash

# Exit on error
set -e
#!/bin/bash
# Mount the local directory to Minikube
# Note that this command blocks, so run it in the background or in a separate terminal
minikube mount /mnt/c/development/argus/dags:/mnt/dags &

# Enable necessary Minikube addons
minikube addons enable ingress
minikube addons enable storage-provisioner

# Notes:
# - The `minikube mount` command must be kept running to keep the mount active.
# - You may need to adapt Minikube start parameters (like VM driver) according to your system setup.
# - Ensure Helm 3 or above is used to avoid needing Tiller in your Kubernetes cluster.

# Set Docker env
eval $(minikube -p minikube docker-env)

# Move to the script's directory

# Build the custom Airflow Docker image
echo "Storing secrets in Kube..."
bash ./scripts/generate_secrets.sh
echo "Building Airflow Docker image..."
docker build -t argus-airflow:latest ./docker/airflow

# Add the Apache Airflow Helm repository
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# Install or Upgrade Airflow using Helm
echo "Deploying Airflow..."
helm upgrade --install \
    --namespace argus \
    --create-namespace \
    --values ./config/airflow/values.yml \
    my-airflow-release \
    apache-airflow/airflow

echo "Airflow should now be deploying. Monitor the pods using: kubectl get pods --namespace airflow -w"
