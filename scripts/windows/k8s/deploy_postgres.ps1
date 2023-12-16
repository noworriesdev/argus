$namespace = $args[0]
$directoryPath = $args[1]
$secretName = $args[2]

# Check if all pods are running
function AllPodsRunning {
    $pods = kubectl get pods --namespace $namespace `
             -l "release=${namespace}-postgres-postgresql-0" `
             -o jsonpath="{.items[*].status.phase}"
    
    return $pods -notcontains "Pending" `
        -and $pods -notcontains "ContainerCreating" `
        -and $pods -notcontains "Failed" `
        -and $pods -notcontains "Unknown"
}

Write-Host "Building PostGres Docker image..."
docker build -t argus-postgres:latest .\docker\postgres

helm install argus-postgres oci://registry-1.docker.io/bitnamicharts/postgresql --set image.repository=argus-postgres,image.tag=latest,image.pullPolicy=IfNotPresent

Write-Host "Deployment initiated. Monitoring status..."

# Monitor pods until they are running
do {
    Start-Sleep -Seconds 10
    Write-Host "Checking pod status..."
} until (AllPodsRunning)

Write-Host "All pods are now running."
Start-Sleep -s 15
# You should be able to configure password via Helm chart but that's not working for some reason.
$encodedString = kubectl get secret --namespace argus argus-postgres-postgresql -o jsonpath="{.data.postgres-password}"
$decodedBytes = [System.Convert]::FromBase64String($encodedString)
$POSTGRES_PASSWORD = [System.Text.Encoding]::UTF8.GetString($decodedBytes)

Write-Host "POSTGRES PASSWORD: ${POSTGRES_PASSWORD}"
Start-Sleep -s 30
Start-Job -ScriptBlock {
    kubectl port-forward svc/$using:namespace-postgres-postgresql 5432:5432
}