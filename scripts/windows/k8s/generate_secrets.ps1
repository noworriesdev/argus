# Define secret name
$NAMESPACE = $args[0]
$SECRET_NAME = $args[1]

# Begin creating the secret.yaml file
@"
apiVersion: v1
kind: Secret
metadata:
  name: $SECRET_NAME
  namespace: $NAMESPACE
type: Opaque
data:
"@ | Out-File secret.yaml

# Read .env file and add keys and base64 encoded values to the secret.yaml
Get-Content .env | ForEach-Object {
    # Split the line into key and value
    $key, $value = $_ -split '=', 2

    # Ensure non-empty key
    if (-not $key) { continue }

    # Skip commented lines
    if ($key -match '^#') { continue }

    # Encode value
    $base64Value = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($value))

    # Add key and base64 encoded value to the secret.yaml
    "  ${key}: $base64Value" | Out-File secret.yaml -Append
}

# Apply the secret.yaml using kubectl
kubectl apply -f secret.yaml --namespace $NAMESPACE

# Optional: Clean up the secret.yaml file
Remove-Item secret.yaml -Force
