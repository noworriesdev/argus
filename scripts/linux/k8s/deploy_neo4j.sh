#!/bin/bash

# Exit on error
set -e

# Constants
CSV_DIR="local_data/csvs"
SCRIPT_PATH="scripts/local/generate_csv_for_import.py"
NEO4J_REPO="https://helm.neo4j.com/neo4j"
VALUES_FILE="./config/neo4j/values.yml"

# Functions

all_pods_running() {
    local pods
    pods=$(kubectl get pods --namespace "$1" -l "release=${1}-neo4j" -o jsonpath="{.items[*].status.phase}")
    [[ "$pods" != *"Pending"* && "$pods" != *"ContainerCreating"* && "$pods" != *"Failed"* && "$pods" != *"Unknown"* ]]
}

# Main logic

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <namespace> <directoryPath>"
    exit 1
fi

namespace="$1"
directoryPath="$2"

if [ -d "$directoryPath/$CSV_DIR" ]; then
    if [ -z "$(ls -A $directoryPath/$CSV_DIR)" ]; then
        python "$directoryPath/$SCRIPT_PATH"
        echo "CSVs are ready for import."
    else
        echo "CSV directory is not empty."
    fi
else
    echo "CSV directory does not exist."
    exit 1
fi

helm repo add neo4j $NEO4J_REPO
helm repo update

echo "Starting Neo4j in offline mode for import..."
helm upgrade --install \
    --namespace "$namespace" \
    --values "$VALUES_FILE" \
    "${namespace}-neo4j" neo4j/neo4j \
    --set neo4j.offlineMaintenanceModeEnabled=true

sleep 15

echo "Copying files for import."
kubectl cp "./$CSV_DIR" "$namespace/${namespace}-neo4j-0:/import/files-1"
echo "Initiating import."
kubectl exec -n "$namespace" "${namespace}-neo4j-0" -- \
    neo4j-admin database import full \
    --nodes=/import/files-1/users.csv \
    --nodes=/import/files-1/channels.csv \
    --nodes=/import/files-1/messages.csv \
    --relationships=/import/files-1/message_channel_rel.csv \
    --relationships=/import/files-1/user_message_rel.csv neo4j \
    --overwrite-destination \
    --multiline-fields=true

echo "Re-launching in regular mode."
helm upgrade --install \
    --namespace "$namespace" \
    --values "$VALUES_FILE" \
    "${namespace}-neo4j" neo4j/neo4j

echo "Deployment initiated. Monitoring status..."

while ! all_pods_running "$namespace"; do
    sleep 10
    echo "Checking pod status..."
done

echo "All pods are now running."
sleep 5

kubectl port-forward svc/"$namespace"-neo4j tcp-bolt tcp-http tcp-https &

# Note: This script backgrounds the port-forward command.
# You may want to capture its PID and kill it later if needed.
