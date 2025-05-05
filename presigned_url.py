import os
import datetime
from google.cloud import storage

def get_presigned_url(file_name: str):
    try:
        creds_path = os.getenv("GCP_SA_KEY")
        gcs = storage.Client.from_service_account_json(creds_path)
        bucket_name = os.getenv("GCP_BUCKET_NAME")
    
        bucket = gcs.get_bucket(bucket_name)
        file_to_send = bucket.get_blob(file_name)
        if file_to_send:
            url = file_to_send.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=60),
                method="GET",
            )

        return url
    except Exception as e:
        print(f"Error al generar URL prefirmada: {e}")
        raise
