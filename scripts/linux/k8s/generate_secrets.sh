#!/bin/bash

# Exit on error
set -e

# Check if namespace and secret_name arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <namespace> <secret_name>"
    exit 1
fi

NAMESPACE="$1"
SECRET_NAME="$2"

# Begin creating the secret.yaml file
cat << EOF > secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: $SECRET_NAME
  namespace: $NAMESPACE
type: Opaque
data:
EOF

# Read .env file and add keys and base64 encoded values to the secret.yaml
while IFS="=" read -r key value
do
    # Ensure non-empty key
    [ -z "$key" ] && continue

    # Skip commented lines
    [[ $key == \#* ]] && continue

    # Encode value
    base64Value=$(echo -n "$value" | base64)

    # Add key and base64 encoded value to the secret.yaml
    echo "  $key: $base64Value" >> secret.yaml

done < .env

# Apply the secret.yaml using kubectl
kubectl apply -f secret.yaml --namespace $NAMESPACE

# Optional: Clean up the secret.yaml file
rm -f secret.yaml
