import os
import sys
import google.auth
from google.auth import impersonated_credentials
from google.cloud import storage

def err(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)

def get_impersonated_creds(target_sa_email: str, scopes: list[str]):
    """
    Uses the build's service account (ADC) as source credentials and
    exchanges them for short-lived credentials of the target service account.
    """
    # Source creds = the Cloud Build runner SA (picked up automatically)
    source_creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

    # Create impersonated credentials for the target SA
    return impersonated_credentials.Credentials(
        source_credentials=source_creds,
        target_principal=target_sa_email,
        target_scopes=scopes,
        lifetime=3600,  # max 1 hour
    )

def list_bucket_objects(bucket_name: str, creds):
    client = storage.Client(credentials=creds)
    print(f"Listing objects in gs://{bucket_name}")
    found = False
    for blob in client.list_blobs(bucket_name):
        print(f"- {blob.name}")
        found = True
    if not found:
        print("(no objects found)")
    print("Done.")

if __name__ == "__main__":
    target_sa = os.getenv("TARGET_SA_EMAIL")
    bucket = os.getenv("BUCKET_NAME")

    if not target_sa:
        err("TARGET_SA_EMAIL is not set"); sys.exit(2)
    if not bucket:
        err("BUCKET_NAME is not set"); sys.exit(2)

    print(f"Target SA to impersonate: {target_sa}")
    print(f"Bucket: {bucket}")

    scopes = ["https://www.googleapis.com/auth/devstorage.read_only"]
    try:
        imp_creds = get_impersonated_creds(target_sa, scopes)
        list_bucket_objects(bucket, imp_creds)
    except Exception as e:
        err(f"Impersonation or GCS call failed: {e}")
        sys.exit(1)

