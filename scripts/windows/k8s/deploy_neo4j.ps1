# Define namespace from the argument
$namespace = $args[0]

# Add neo4j helm repository and update
helm repo add neo4j https://helm.neo4j.com/neo4j
helm repo update

Write-Host "Initiating deployment..."
helm upgrade --install --namespace $namespace --values .\config\neo4j\values.yml $namespace-neo4j neo4j/neo4j 
Write-Host "Deployment initiated. Monitoring status..."

# Function to check if all pods are running
function AllPodsRunning {
    $pods = kubectl get pods --namespace $namespace -l "release=${namespace}-neo4j" -o jsonpath="{.items[*].status.phase}"
    return $pods -notcontains "Pending" -and $pods -notcontains "ContainerCreating" -and $pods -notcontains "Failed" -and $pods -notcontains "Unknown"
}

# Wait until all pods are running
do {
    Start-Sleep -Seconds 10
    Write-Host "Checking pod status..."
} until (AllPodsRunning)

Write-Host "All pods are now running."
Write-Host "Copying files for import."
kubectl cp local_data/csvs argus/argus-neo4j-0:/import/files-1

Start-Sleep -Seconds 5
# Port forward with kubectl
Start-Process -NoNewWindow kubectl -ArgumentList "port-forward svc/${namespace}-neo4j tcp-bolt tcp-http tcp-https"
