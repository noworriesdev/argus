# Mount the directory to Minikube
Start-Process -NoNewWindow minikube -ArgumentList "mount C:\development\argus\local_data:/mnt/argus"

# Enable necessary Minikube addons
minikube addons enable ingress
minikube addons enable storage-provisioner

<#
Notes:
- The `minikube mount` command must be kept running to keep the mount active.
#>

# Set Docker env
Invoke-Expression -Command (minikube -p minikube docker-env | Out-String)
