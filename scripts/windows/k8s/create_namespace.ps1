# Check if the namespace already exists, create if not
$namespace = $args[0]

# Initialize the variable
$namespaceExists = $false

# Check namespace existence
try {
    kubectl get namespace $namespace > $null 2>&1 -ErrorAction SilentlyContinue
    if ($LASTEXITCODE -eq 0) {
        $namespaceExists = $true
    }
} catch {
    # Do nothing, just continue as namespaceExists will remain $false
}

if ($namespaceExists) {
    Write-Host "Namespace '$namespace' already exists. Skipping creation."
} else {
    # Create the namespace
    kubectl create namespace $namespace
    Write-Host "Namespace '$namespace' created."
}

kubectl config set-context minikube --namespace=$namespace
