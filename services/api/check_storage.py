"""S3 emulator diagnostic; no public bucket and no external provider."""

import json
import os
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from growth.storage import S3Storage

client = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY"],
    aws_secret_access_key=os.environ["S3_SECRET_KEY"],
    region_name="us-east-1",
    config=Config(
        signature_version="s3v4", s3={"addressing_style": "path"}, connect_timeout=3, read_timeout=5
    ),
)
bucket = "growth-diagnostic-" + uuid.uuid4().hex[:16]
client.create_bucket(Bucket=bucket)
storage = S3Storage(client, bucket)
a, b = uuid.uuid4().hex, uuid.uuid4().hex
key = None
try:
    key = storage.put(a, "fixture.txt", b"private-storage-fixture", "text/plain")
    assert storage.get(a, "fixture.txt") == b"private-storage-fixture"
    try:
        storage.get(b, "fixture.txt")
    except ClientError as exc:
        assert exc.response["Error"]["Code"] in {"NoSuchKey", "404"}
    else:
        raise AssertionError("Cross-workspace key resolved")
    print(
        json.dumps(
            {
                "storage": "S3-compatible local emulator",
                "roundtrip": "passed",
                "workspace_prefix_isolation": "passed",
            }
        )
    )
finally:
    if key:
        client.delete_object(Bucket=bucket, Key=key)
    client.delete_bucket(Bucket=bucket)
