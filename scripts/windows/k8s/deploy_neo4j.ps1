# Variables from arguments
$namespace = $args[0]
$directoryPath = $args[1]

# Check for CSV directory and generate if necessary
function CheckAndGenerateCSV {
    $csvPath = "$directoryPath\local_data\csvs"
    
    if (Test-Path $csvPath -PathType Container) {
        # Get all items in the directory
        $items = Get-ChildItem -Path $csvPath

        if ($items.Count -eq 0) {
            # Run Python script to generate CSVs
            $pythonScript = "$directoryPath\scripts\local\generate_csv_for_import.py"
            python $pythonScript
            Write-Output "CSVs are ready for import."
        } else {
            Write-Output "CSV directory is not empty."
        }
    } else {
        Write-Error "CSV directory does not exist."
    }
}

# Add and update neo4j helm repository
function UpdateHelmRepository {
    helm repo add neo4j https://helm.neo4j.com/neo4j
    helm repo update
}

# Check if all pods are running
function AllPodsRunning {
    $pods = kubectl get pods --namespace $namespace `
             -l "release=${namespace}-neo4j" `
             -o jsonpath="{.items[*].status.phase}"
    
    return $pods -notcontains "Pending" `
        -and $pods -notcontains "ContainerCreating" `
        -and $pods -notcontains "Failed" `
        -and $pods -notcontains "Unknown"
}

# Main script execution
CheckAndGenerateCSV
UpdateHelmRepository

Write-Host "Starting Neo4j in offline mode for import..."
helm upgrade --install `
    --namespace $namespace `
    --values .\config\neo4j\values.yml `
    $namespace-neo4j neo4j/neo4j `
    --set neo4j.offlineMaintenanceModeEnabled=true

Start-Sleep -Seconds 30

Write-Host "Copying files for import."
kubectl cp ./local_data/csvs argus/argus-neo4j-0:/import/files-1

Write-Host "Initiating import."
kubectl exec -n argus argus-neo4j-0 `
    -- neo4j-admin database import full `
    --nodes=User=/import/files-1/users.csv `
    --nodes=Channel=/import/files-1/channels.csv `
    --nodes=Message=/import/files-1/messages.csv `
    --nodes=Reaction=/import/files-1/reactions.csv `
    --relationships=/import/files-1/message_channel_rel.csv `
    --relationships=/import/files-1/user_message_rel.csv `
    --relationships=/import/files-1/user_reaction_rel.csv `
    --relationships=/import/files-1/message_reaction_rel.csv `
    --relationships=/import/files-1/message_mention_rel.csv `
    --overwrite-destination `
    --multiline-fields=true

Write-Host "Re-launching in regular mode."
helm upgrade --install `
    --namespace $namespace `
    --values .\config\neo4j\values.yml `
    $namespace-neo4j neo4j/neo4j

Write-Host "Neo4j Deployment initiated. Monitoring status..."

# Monitor pods until they are running
do {
    Start-Sleep -Seconds 30
    Write-Host "Checking pod status..."
} until (AllPodsRunning)

Write-Host "All pods are now running."

Start-Sleep -Seconds 5
# Port forward with kubectl
Start-Process -NoNewWindow kubectl `
    -ArgumentList "port-forward svc/${namespace}-neo4j tcp-bolt tcp-http"
