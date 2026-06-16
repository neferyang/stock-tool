#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trigger GitHub Actions workflow directly
"""

import subprocess
import json
import urllib.request
import urllib.error
import sys

# Get GitHub token from git credential
try:
    process = subprocess.Popen(
        ["git", "credential", "fill"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input="host=github.com\nprotocol=https\n")

    token = None
    for line in stdout.split("\n"):
        if line.startswith("password="):
            token = line.split("=", 1)[1]
            break

    if not token:
        print("[ERROR] Failed to get GitHub token")
        sys.exit(1)

    print("[OK] GitHub token obtained")

except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Trigger workflow
url = "https://api.github.com/repos/neferyang/stock-tool/actions/workflows/update-financial-data.yml/dispatches"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
}

body = json.dumps({"ref": "main"}).encode('utf-8')

print("\n[INFO] Triggering workflow via GitHub API...")
print(f"[INFO] URL: {url}")

try:
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    response = urllib.request.urlopen(req)

    print(f"[OK] Workflow triggered! (HTTP {response.status})")

except urllib.error.HTTPError as e:
    if e.code == 204:
        print("[OK] Workflow triggered! (HTTP 204)")
    else:
        print(f"[ERROR] HTTP {e.code}: {e.reason}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"[ERROR] Response: {error_body}")
        except:
            pass
        sys.exit(1)
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

print("\n[INFO] Workflow is running in background...")
print("[INFO] Please wait 5-10 minutes for completion...")
print("[INFO] Check progress at: https://github.com/neferyang/stock-tool/actions")
