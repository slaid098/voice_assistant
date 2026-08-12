"""Create Forgejo release and upload asset. Called from release.yml.

Idempotent: if a release for this tag already exists (e.g. from a previous
failed run), it is deleted before creating a new one. This prevents
HTTP 409 Conflict errors.
"""

import json
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from scripts.release_notes import extract_changelog_section

server = os.environ["GITHUB_SERVER_URL"]
token = os.environ["GITHUB_TOKEN"]
tag = os.environ["GITHUB_REF_NAME"]
repo = "slaid098/voice_assistant"
headers = {"Authorization": f"token {token}"}


def api_request(path: str, method: str = "GET", data: bytes | None = None) -> object:
    url = f"{server}/api/v1/repos/{repo}/{path}"
    req = urllib.request.Request(  # noqa: S310
        url,
        data=data,
        headers={**headers, "Content-Type": "application/json"} if data else headers,
        method=method,
    )
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        body = resp.read()
        return json.loads(body) if body else None


note = extract_changelog_section(Path("CHANGELOG.md"), tag)

# Delete existing release for this tag if present (idempotency)
try:
    existing = api_request("releases")
    for rel in existing if isinstance(existing, list) else []:
        if rel.get("tag_name") == tag:
            print(f"Deleting existing release id={rel['id']} for tag={tag}")
            api_request(f"releases/{rel['id']}", method="DELETE")
except urllib.error.HTTPError:
    pass

# Create release
data = json.dumps({"tag_name": tag, "name": tag, "body": note}).encode()
release = api_request("releases", method="POST", data=data)
release_id = release["id"]  # type: ignore[index]
print(f"Release created: id={release_id}, tag={tag}")

# Upload asset using multipart/form-data
boundary = uuid.uuid4().hex
with open("dist/voice-assistant.zip", "rb") as f:
    file_data = f.read()

body = (
    (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="attachment"; filename="voice-assistant.zip"\r\n'
        f"Content-Type: application/zip\r\n\r\n"
    ).encode()
    + file_data
    + f"\r\n--{boundary}--\r\n".encode()
)

upload_url = f"{server}/api/v1/repos/{repo}/releases/{release_id}/assets"
req = urllib.request.Request(  # noqa: S310
    f"{upload_url}?name=voice-assistant.zip",
    data=body,
    headers={
        "Authorization": f"token {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    },
    method="POST",
)
with urllib.request.urlopen(req) as resp:  # noqa: S310
    asset = json.loads(resp.read())
    print(f"Asset uploaded: {asset.get('name')}, size={asset.get('size', 0) // 1024 // 1024}MB")
