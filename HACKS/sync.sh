#!/bin/bash

while true; do
    echo "[$(date)] Starting GCS sync..."

    gsutil -m rsync -r ./local/folder gs://path/to/gcs

    echo "[$(date)] Sync completed."

    sleep 900
done