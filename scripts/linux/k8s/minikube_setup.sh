#!/bin/bash

# Exit on error
set -e

# Check if directory_path argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory_path>"
    exit 1
fi

directory_path="$1"

# Mount the directory to Minikube
# Note: You might want to run this command in a separate terminal 
# because it needs to keep running to maintain the mount.
minikube mount "$directory_path:/mnt/argus" &

# Give it a few seconds to ensure the mount is active
sleep 5

# Enable necessary Minikube addons
minikube addons enable ingress
minikube addons enable storage-provisioner

# Notes:
# The `minikube mount` command must be kept running to keep the mount active.

# Set Docker env
eval $(minikube -p minikube docker-env)
