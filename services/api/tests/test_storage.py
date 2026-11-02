from io import BytesIO
from unittest.mock import MagicMock

import pytest

from growth.security import Problem
from growth.storage import S3Storage


def test_storage_prefix_validation_size_and_stream_closing():
    client = MagicMock()
    storage = S3Storage(client, "private-bucket")
    a, b = "a" * 32, "b" * 32
    assert storage.put(a, "image.png", b"image", "image/png") == "workspaces/" + a + "/image.png"
    assert storage.key(a, "image.png") != storage.key(b, "image.png")
    stream = BytesIO(b"body")
    client.get_object.return_value = {"Body": stream}
    assert storage.get(a, "image.png") == b"body" and stream.closed
    for name in ("../escape", "https://internal", "/absolute", "nested/key"):
        with pytest.raises(Problem):
            storage.put(a, name, b"body", "text/plain")
    with pytest.raises(Problem):
        storage.put("invalid", "name", b"x", "text/plain")
    with pytest.raises(Problem):
        storage.put(a, "name", b"x" * (10 * 1024 * 1024 + 1), "text/plain")
    with pytest.raises(Problem):
        storage.put(a, "name", b"x", "text/plain\r\nHeader:value")
