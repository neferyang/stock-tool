#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check GitHub Actions workflow logs
"""

import subprocess
import json
import urllib.request
import urllib.error
import sys

def get_token():
    """Get GitHub token"""
    try:
        process = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, _ = process.communicate(input="host=github.com\nprotocol=https\n")
        for line in stdout.split("\n"):
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except:
        pass
    return None

def get_workflow_logs(token):
    """Get latest workflow logs"""
    # First, get the latest run ID
    url = "https://api.github.com/repos/neferyang/stock-tool/actions/runs?per_page=1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        runs = data.get('workflow_runs', [])

        if not runs:
            print("[INFO] No workflow runs found")
            return

        run_id = runs[0]['id']
        run_name = runs[0].get('name', 'Unknown')
        run_status = runs[0].get('status', 'unknown')
        run_conclusion = runs[0].get('conclusion')

        print(f"[INFO] Latest Workflow Run")
        print(f"[INFO] Name: {run_name}")
        print(f"[INFO] Status: {run_status}")
        print(f"[INFO] Conclusion: {run_conclusion}")
        print(f"[INFO] Run ID: {run_id}")
        print("\n[INFO] Fetching job details...\n")

        # Get jobs for this run
        jobs_url = f"https://api.github.com/repos/neferyang/stock-tool/actions/runs/{run_id}/jobs"
        req = urllib.request.Request(jobs_url, headers=headers)
        response = urllib.request.urlopen(req)
        jobs_data = json.loads(response.read().decode('utf-8'))
        jobs = jobs_data.get('jobs', [])

        for job in jobs:
            job_name = job.get('name', 'Unknown')
            job_status = job.get('status', 'unknown')
            job_conclusion = job.get('conclusion')
            job_id = job.get('id')

            print(f"[JOB] {job_name}")
            print(f"      Status: {job_status}")
            print(f"      Conclusion: {job_conclusion}")

            # Get steps for this job
            steps = job.get('steps', [])
            if steps:
                print(f"      Steps:")
                for step in steps:
                    step_name = step.get('name', 'Unknown')
                    step_status = step.get('status', 'unknown')
                    step_conclusion = step.get('conclusion')

                    status_symbol = "✓" if step_conclusion == "success" else ("✗" if step_conclusion == "failure" else "⟳")
                    print(f"        {status_symbol} {step_name}: {step_conclusion}")

            # Get logs URL
            logs_url = job.get('logs_url')
            if logs_url and job_conclusion == "failure":
                print(f"\n[INFO] Fetching error logs for failed job: {job_name}\n")
                try:
                    req = urllib.request.Request(logs_url, headers=headers)
                    response = urllib.request.urlopen(req)
                    logs = response.read().decode('utf-8')

                    # Print last 50 lines of logs
                    log_lines = logs.split('\n')
                    print("[LOGS] Last 50 lines of logs:")
                    print("=" * 60)
                    for line in log_lines[-50:]:
                        if line.strip():
                            print(line)
                    print("=" * 60)
                except urllib.error.HTTPError as e:
                    print(f"[INFO] Could not fetch logs: {e.code}")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    token = get_token()
    if not token:
        print("[ERROR] Could not get GitHub token")
        sys.exit(1)

    get_workflow_logs(token)
