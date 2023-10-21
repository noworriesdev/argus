#!/bin/bash

# Exit on error
set -e

# Check if the namespace argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <namespace>"
    exit 1
fi

namespace="$1"

# Check namespace existence
if kubectl get namespace "$namespace" &>/dev/null; then
    echo "Namespace '$namespace' already exists. Skipping creation."
else
    # Create the namespace
    kubectl create namespace "$namespace"
    echo "Namespace '$namespace' created."
fi

kubectl config set-context minikube --namespace="$namespace"
