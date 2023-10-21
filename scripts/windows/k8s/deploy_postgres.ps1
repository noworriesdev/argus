$namespace = $args[0]
$directoryPath = $args[1]

helm install argus-postgres oci://registry-1.docker.io/bitnamicharts/postgresql

$POSTGRES_PASSWORD = kubectl get secret --namespace argus argus-postgres-postgresql -o jsonpath="{.data.postgres-password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
Write-Host "Your Postgres password is..."
Write-Output $POSTGRES_PASSWORD

kubectl port-forward svc/argus-postgres-postgresql 5432:5432
