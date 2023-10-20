# Define the directory path and Python file path
$directoryPath = $args[0]

# Check if the directory exists
if (Test-Path $directoryPath\local_data\csvs -PathType Container) {
    # Get all items in the directory
    $items = Get-ChildItem -Path $directoryPath\local_data\csvs

    # If the directory is empty, run the Python file
    if ($items.Count -eq 0) {
        # Ensure python is in your PATH or provide full path to python.exe
        python $directoryPath\scripts\local\generate_csv_for_import.py
        Write-Output "CSVs are ready for import."
    } else {
        Write-Output "CSV directory is not empty."
    }
} else {
    Write-Error "CSV directory does not exist."
}

kubectl cp ./local_data/csvs argus/argus-neo4j-0:/import/files-1
kubectl exec -n argus argus-neo4j-0 -- neo4j-admin database import full --nodes=/import/files-1/users.csv --nodes=/import/files-1/channels.csv --nodes=/import/files-1/messages.csv --relationships=/import/files-1/message_channel_rel.csv --relationships=/import/files-1/user_message_rel.csv neo4j --overwrite-destination --multiline-fields=true



