namespace="$1"

helm repo add neo4j https://helm.neo4j.com/neo4j
helm repo update
echo "Initiating deployment..."
helm upgrade --install \
    --namespace $namespace \
    --values ./config/neo4j/values.yml \
    $namespace-neo4j \
    neo4j/neo4j \
    > /dev/null
echo "Deployment initiated. Monitoring status..."
sleep 45
kubectl port-forward svc/argus-neo4j tcp-bolt tcp-http tcp-https &