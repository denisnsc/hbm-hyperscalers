"""
Deploys the HBM & Hyperscalers terminal directly to GitHub Pages using the GitHub REST API
(works even when Git is not installed on Windows).

Usage:
  python deploy_github_pages.py --token YOUR_GITHUB_PAT --repo hbm-hyperscalers
"""

import argparse
import base64
from pathlib import Path
import requests

PROJECT_DIR = Path(__file__).resolve().parent
FILES_TO_UPLOAD = [
    "index.html",
    "dashboard.html",
    "portfolio_config.json",
    "portfolio_data.json",
    "fetch_portfolio_data.py",
    "build_dashboard.py",
    "update_dashboard.py",
    "requirements.txt",
    "DECISIONS.md",
    ".github/workflows/update_pages.yml",
]


def upload_all_in_single_commit(session: requests.Session, owner: str, repo: str, single_root_commit: bool = True):
    """Uploads all FILES_TO_UPLOAD in a single Git commit via the GitHub Git Data API."""
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Get current main branch commit & tree
    ref_resp = session.get(f"{base_url}/git/ref/heads/main")
    if ref_resp.status_code != 200:
        raise RuntimeError(f"Could not read branch main: {ref_resp.status_code} {ref_resp.text}")
    latest_commit_sha = ref_resp.json()["object"]["sha"]

    tree_items = []
    for rel_path in FILES_TO_UPLOAD:
        local_path = PROJECT_DIR / rel_path
        if not local_path.exists():
            continue
        blob_resp = session.post(f"{base_url}/git/blobs", json={
            "content": base64.b64encode(local_path.read_bytes()).decode("ascii"),
            "encoding": "base64",
        })
        if blob_resp.status_code != 201:
            if "workflow" in rel_path:
                print(f"  Note: Skipped {rel_path} (token lacks 'workflow' scope).")
                continue
            raise RuntimeError(f"Failed creating blob for {rel_path}: {blob_resp.status_code} {blob_resp.text}")
        tree_items.append({
            "path": rel_path,
            "mode": "100644",
            "type": "blob",
            "sha": blob_resp.json()["sha"],
        })
        print(f"  Staged {rel_path}")

    tree_resp = session.post(f"{base_url}/git/trees", json={"tree": tree_items})
    if tree_resp.status_code != 201:
        raise RuntimeError(f"Failed creating tree: {tree_resp.status_code} {tree_resp.text}")

    # Create a single commit (orphan root commit if single_root_commit=True to replace the 10-commit history with 1 commit)
    commit_payload = {
        "message": "HBM & Hyperscalers interactive valuation & performance terminal",
        "tree": tree_resp.json()["sha"],
        "parents": [] if single_root_commit else [latest_commit_sha],
    }
    commit_resp = session.post(f"{base_url}/git/commits", json=commit_payload)
    if commit_resp.status_code != 201:
        raise RuntimeError(f"Failed creating commit: {commit_resp.status_code} {commit_resp.text}")

    new_commit_sha = commit_resp.json()["sha"]
    update_ref = session.patch(f"{base_url}/git/refs/heads/main", json={
        "sha": new_commit_sha,
        "force": True,
    })
    if update_ref.status_code != 200:
        raise RuntimeError(f"Failed updating main ref: {update_ref.status_code} {update_ref.text}")
    print(f"  Committed all files in 1 single commit ({new_commit_sha[:7]})")


def main():
    parser = argparse.ArgumentParser(description="Publish HBM & Hyperscalers Dashboard to GitHub Pages")
    parser.add_argument("--token", required=True, help="GitHub Personal Access Token (with repo & workflow scope)")
    parser.add_argument("--repo", default="hbm-hyperscalers", help="Repository name to create/update")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {args.token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })

    # 1. Get authenticated username
    user_resp = session.get("https://api.github.com/user")
    if user_resp.status_code != 200:
        raise RuntimeError(f"GitHub authentication failed: {user_resp.status_code} {user_resp.text}")
    owner = user_resp.json()["login"]
    print(f"Authenticated as GitHub user: {owner}")

    # 2. Create repository if it does not exist
    repo_check = session.get(f"https://api.github.com/repos/{owner}/{args.repo}")
    if repo_check.status_code == 404:
        print(f"Creating public repository {owner}/{args.repo}...")
        create_resp = session.post("https://api.github.com/user/repos", json={
            "name": args.repo,
            "description": "Interactive HBM, Hyperscalers & AI Infrastructure Market Valuation & Performance Terminal",
            "private": False,
            "auto_init": True,
        })
        if create_resp.status_code not in (200, 201):
            raise RuntimeError(f"Could not create repo: {create_resp.status_code} {create_resp.text}")
    else:
        print(f"Using existing repository {owner}/{args.repo}...")

    # 3. Upload all project files in 1 single commit
    upload_all_in_single_commit(session, owner, args.repo, single_root_commit=True)

    # 4. Enable GitHub Pages on main branch root
    pages_url = f"https://api.github.com/repos/{owner}/{args.repo}/pages"
    pages_check = session.get(pages_url)
    if pages_check.status_code == 404:
        print("Enabling GitHub Pages on branch 'main' (/ root)...")
        session.post(pages_url, json={"source": {"branch": "main", "path": "/"}})

    live_url = f"https://{owner}.github.io/{args.repo}/"
    print(f"\nSUCCESS! Your dashboard will be live in ~30-60 seconds at:\n  {live_url}")


if __name__ == "__main__":
    main()
