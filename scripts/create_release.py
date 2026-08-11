"""Create Forgejo release and upload asset. Called from release.yml."""

import json
import os
import urllib.request
import uuid

server = os.environ["GITHUB_SERVER_URL"]
token = os.environ["GITHUB_TOKEN"]
tag = os.environ["GITHUB_REF_NAME"]
repo = "slaid098/voice_assistant"

with open("CHANGELOG.md", encoding="utf-8") as f:
    note = f.read()

# Create release
data = json.dumps({"tag_name": tag, "name": tag, "body": note}).encode()
req = urllib.request.Request(  # noqa: S310
    f"{server}/api/v1/repos/{repo}/releases",
    data=data,
    headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:  # noqa: S310
    release = json.loads(resp.read())
    release_id = release["id"]
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
