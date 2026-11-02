"""Private S3-compatible storage. Callers must authenticate before selecting a workspace."""

import re

from .security import Problem


class S3Storage:
    def __init__(self, client, bucket):
        self.client, self.bucket = client, bucket

    @staticmethod
    def key(workspace, name):
        if not re.fullmatch(r"[0-9a-f]{32}", workspace) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}", name
        ):
            raise Problem("validation", "Invalid workspace or object name")
        return f"workspaces/{workspace}/{name}"

    def put(self, workspace_id, name, body, content_type):
        key = self.key(workspace_id, name)
        if not isinstance(body, bytes) or len(body) > 10 * 1024 * 1024:
            raise Problem("validation", "Object limit is 10 MiB")
        if (
            not isinstance(content_type, str)
            or len(content_type) > 100
            or "\n" in content_type
            or "\r" in content_type
        ):
            raise Problem("validation", "Invalid object content type")
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body, ContentType=content_type)
        return key

    def get(self, workspace_id, name):
        response = self.client.get_object(Bucket=self.bucket, Key=self.key(workspace_id, name))
        body = response["Body"]
        try:
            value = body.read(10 * 1024 * 1024 + 1)
            if len(value) > 10 * 1024 * 1024:
                raise Problem("too_large", "Stored object exceeds size limit", 413)
            return value
        finally:
            body.close()
