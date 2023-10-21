#!/bin/bash

# Get all processes with 'kubectl port-forward' in the command line and kill them
pids=$(pgrep -f "kubectl.*port-forward")
for pid in $pids; do
    echo "Killing process with ID $pid ..."
    kill -9 $pid
done

echo "All 'kubectl port-forward' processes have been killed."

# Execute the Kubernetes and Minikube commands
helm uninstall argus-neo4j --namespace argus
kubectl delete namespace argus
minikube stop
minikube start
