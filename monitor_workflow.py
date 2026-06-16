#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor GitHub Actions workflow progress in real-time
"""

import subprocess
import json
import urllib.request
import urllib.error
import time
import sys

def get_token():
    """Get GitHub token from git credential"""
    try:
        process = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input="host=github.com\nprotocol=https\n")

        for line in stdout.split("\n"):
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except:
        pass
    return None

def get_workflow_runs(token):
    """Get latest workflow runs"""
    url = "https://api.github.com/repos/neferyang/stock-tool/actions/runs?per_page=1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        return data.get('workflow_runs', [])
    except:
        return []

def monitor_workflow():
    """Monitor workflow progress"""
    token = get_token()
    if not token:
        print("[ERROR] Could not get GitHub token")
        return

    print("[INFO] Monitoring workflow progress...")
    print("[INFO] (Updates every 10 seconds, press Ctrl+C to stop)\n")

    max_attempts = 60  # 10 minutes
    attempt = 0
    last_status = None

    while attempt < max_attempts:
        runs = get_workflow_runs(token)

        if runs:
            run = runs[0]
            status = run.get('status', 'unknown')
            conclusion = run.get('conclusion')
            name = run.get('name', 'Unknown')
            created_at = run.get('created_at', 'unknown')

            if status != last_status:
                print(f"\n[PROGRESS] Workflow: {name}")
                print(f"[PROGRESS] Status: {status}")
                if conclusion:
                    print(f"[PROGRESS] Conclusion: {conclusion}")
                print(f"[PROGRESS] Started: {created_at}")
                last_status = status

            # Print progress indicator
            if status == 'in_progress':
                print(".", end="", flush=True)
            elif status == 'completed':
                if conclusion == 'success':
                    print("\n\n[SUCCESS] Workflow completed successfully!")
                    print("[SUCCESS] Financial data has been fetched and committed")
                    print("[INFO] Check repository: https://github.com/neferyang/stock-tool")
                    break
                else:
                    print(f"\n\n[WARNING] Workflow completed with: {conclusion}")
                    break

        attempt += 1
        time.sleep(10)

    if attempt >= max_attempts:
        print("\n\n[INFO] Monitoring timeout - workflow may still be running")
        print("[INFO] Check status at: https://github.com/neferyang/stock-tool/actions")

if __name__ == "__main__":
    try:
        monitor_workflow()
    except KeyboardInterrupt:
        print("\n[INFO] Monitoring stopped")
        sys.exit(0)
