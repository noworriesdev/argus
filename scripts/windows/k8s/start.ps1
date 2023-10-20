# Exit on error
$ErrorActionPreference = 'Stop'

# Ensure .env file exists
if (-not (Test-Path .\.env)) {
    Write-Error ".env file not found."
    exit
}

# Declaring main variables
$namespace = "argus"
$secrets_name = "argus-secrets"
$directory_path="C:\development\argus"

# Create namespace if it doesn't exist
& '.\scripts\windows\k8s\create_namespace.ps1' $namespace

Write-Host "Initial config on Minikube..."
& '.\scripts\windows\k8s\minikube_setup.ps1'

Write-Host "Storing secrets in Kube..."
& '.\scripts\windows\k8s\generate_secrets.ps1' $namespace $secrets_name

Write-Host "Deploying Neo4j..."
& '.\scripts\windows\k8s\deploy_neo4j.ps1' $namespace
Write-Host "Loading data into Neo4j with admin import..."
& ".\scripts\windows\k8s\load_neo4j.ps1" $directory_path
<#
Write-Host "Building Airflow Docker image..."
docker build -t argus-airflow:latest .\docker\airflow

# Add the Apache Airflow Helm repository
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# Install or Upgrade Airflow using Helm
Write-Host "Deploying Airflow..."
helm upgrade --install `
    --namespace $namespace `
    --create-namespace `
    --values .\config\airflow\values.yml `
    argus-airflow `
    apache-airflow/airflow

Write-Host "Airflow should now be deploying. Monitor the pods using: kubectl get pods --namespace $namespace -w"
#>

