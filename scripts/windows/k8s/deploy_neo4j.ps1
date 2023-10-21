# Define namespace from the argument
$namespace = $args[0]
$directoryPath = $args[1]
# Logic for CSV generation if they're absent
if (Test-Path $directoryPath\local_data\csvs -PathType Container) {
    # Get all items in the directory
    $items = Get-ChildItem -Path $directoryPath\local_data\csvs

    # If the directory is empty, run the Python file
    if ($items.Count -eq 0) {
        # Ensure python is in your PATH or provide full path to python.exe
        python $directoryPath\scripts\local\generate_csv_for_import.py
        Write-Output "CSVs are ready for import."
    } else {
        Write-Output "CSV directory is not empty."
    }
} else {
    Write-Error "CSV directory does not exist."
}
# Add neo4j helm repository and update
helm repo add neo4j https://helm.neo4j.com/neo4j
helm repo update

Write-Host "Starting Neo4j in offline mode for import..."
helm upgrade --install --namespace $namespace --values .\config\neo4j\values.yml $namespace-neo4j neo4j/neo4j --set neo4j.offlineMaintenanceModeEnabled=true
Start-Sleep -Seconds 5
Write-Host "Copying files for import."
kubectl cp ./local_data/csvs argus/argus-neo4j-0:/import/files-1
Write-Host "Initiating import."
kubectl exec -n argus argus-neo4j-0 -- neo4j-admin database import full --nodes=/import/files-1/users.csv --nodes=/import/files-1/channels.csv --nodes=/import/files-1/messages.csv --relationships=/import/files-1/message_channel_rel.csv --relationships=/import/files-1/user_message_rel.csv neo4j --overwrite-destination --multiline-fields=true
Write-Host "Re-launching in regular mode."
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

Start-Sleep -Seconds 5
# Port forward with kubectl
Start-Process -NoNewWindow kubectl -ArgumentList "port-forward svc/${namespace}-neo4j tcp-bolt tcp-http tcp-https"
