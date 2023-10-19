#!/bin/bash

# Ensure .env file exists
if [[ ! -f .env ]]; then
    echo "Error: .env file not found."
    exit 1
fi

# Define secret name
SECRET_NAME="argus-secrets"

# Begin creating the secret.yaml file
cat <<EOF > secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: $SECRET_NAME
type: Opaque
data:
EOF

# Read .env file and add keys and base64 encoded values to the secret.yaml
while IFS='=' read -r key value || [[ -n "$key" ]]; do
    # Ensure non-empty value
    [ -z "$key" ] && continue
    # Skip commented lines
    [[ $key == \#* ]] && continue
    
    # Add key and base64 encoded value to the secret.yaml
    echo "  $key: $(echo -n "$value" | base64)" >> secret.yaml
done < .env

# Apply the secret.yaml using kubectl
kubectl apply -f secret.yaml --namespace argus

# Optional: Clean up the secret.yaml file
rm -f secret.yaml
