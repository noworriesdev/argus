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

Write-Host "Deploying Postgres..."
& '.\scripts\windows\k8s\deploy_postgres.ps1' $namespace $directory_path $secrets_name

Write-Host "Deploying Airflow..."
& '.\scripts\windows\k8s\deploy_airflow.ps1' $namespace $directory_path $secrets_name

Write-Host "Deploying Neo4j..."
& '.\scripts\windows\k8s\deploy_neo4j.ps1' $namespace $directory_path