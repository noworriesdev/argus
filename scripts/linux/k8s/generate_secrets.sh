# Define secret name
NAMESPACE="$1"
SECRET_NAME="$2"

# Begin creating the secret.yaml file
cat <<EOF > secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: $SECRET_NAME
  namespace: $NAMESPACE
type: Opaque
data:
EOF

# Read .env file and add keys and base64 encoded values to the secret.yaml
while IFS='=' read -r key remaining || [[ -n "$key" ]]; do
    # Ensure non-empty key
    [ -z "$key" ] && continue
    
    # Skip commented lines
    [[ $key == \#* ]] && continue
    
    # Extract and encode value
    # NOTE: assuming that everything after the first '=' sign belongs to the value
    value=$(echo -n "${remaining}" | base64 | tr -d '\n')
    
    # Add key and base64 encoded value to the secret.yaml
    echo "  $key: $value" >> secret.yaml
done < .env

# Apply the secret.yaml using kubectl
kubectl apply -f secret.yaml --namespace argus

# Optional: Clean up the secret.yaml file
rm -f secret.yaml


# Optional: Clean up the secret.yaml file
rm -f secret.yaml