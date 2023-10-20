minikube mount /mnt/c/development/argus:/mnt/argus &

# Enable necessary Minikube addons
minikube addons enable ingress
minikube addons enable storage-provisioner

# Notes:
# - The `minikube mount` command must be kept running to keep the mount active.

# Set Docker env
eval $(minikube -p minikube docker-env)