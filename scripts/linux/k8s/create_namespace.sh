# Check if the namespace already exists, create if not
namespace="$1"
if kubectl get namespace "$namespace" &> /dev/null; then
    echo "Namespace '$namespace' already exists. Skipping creation."
else
    # Create the namespace
    kubectl create namespace "$namespace"
    echo "Namespace '$namespace' created."
fi
kubectl config set-context minikube --namespace=$namespace
