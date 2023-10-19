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
#!/bin/bash

# Ensure .env file exists
if [[ ! -f .env ]]; then
    echo "Error: .env file not found."
    exit 1
fi
# kubectl create namespace argus
# Define secret name
SECRET_NAME="argus-secrets"

# Begin creating the secret.yaml file
cat <<EOF > secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: $SECRET_NAME
  namespace: argus
type: Opaque
data:
EOF

# Read .env file and add keys and base64 encoded values to the secret.yaml
while IFS='=' read -r key remaining || [[ -n "$key" ]]; do
    # Ensure non-empty key
    [ -z "$key" ] && continue
    
    # Skip commented lines
    [[ $key == \#* ]] && continue
    
    # Extract and encode value
    # NOTE: assuming that everything after the first '=' sign belongs to the value
    value=$(echo -n "${remaining}" | base64 | tr -d '\n')
    
    # Add key and base64 encoded value to the secret.yaml
    echo "  $key: $value" >> secret.yaml
done < .env

# Apply the secret.yaml using kubectl
kubectl apply -f secret.yaml --namespace argus

# Optional: Clean up the secret.yaml file
rm -f secret.yaml


# Optional: Clean up the secret.yaml file
rm -f secret.yaml
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
    argus-airflow \
    apache-airflow/airflow

echo "Airflow should now be deploying. Monitor the pods using: kubectl get pods --namespace argus -w"

echo "Deploying Neo4j..."
helm repo add neo4j https://helm.neo4j.com/neo4j
helm repo update
helm upgrade --install \
    --namespace argus \
    --create-namespace \
    --values ./config/neo4j/values.yml \
    argus-neo4j \
    neo4j/neo4j
sleep 2
kubectl port-forward svc/argus-airflow-webserver 8080:8080 --namespace argus 
sleep 45
kubectl port-forward svc/argus-neo4j tcp-bolt tcp-http tcp-https 
