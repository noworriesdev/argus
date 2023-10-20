# Get all processes with 'kubectl port-forward' in the command line
$processes = Get-Process | Where-Object { $_.Description -eq "kubectl" -and $_.CommandLine -like "*port-forward*" }

# Kill each process
$processes | ForEach-Object {
    Write-Output "Killing process with ID $($_.Id) ..."
    Stop-Process -Id $_.Id -Force
}

Write-Output "All 'kubectl port-forward' processes have been killed."

helm uninstall argus-neo4j --namespace argus
kubectl delete namespace argus
minikube stop
minikube start