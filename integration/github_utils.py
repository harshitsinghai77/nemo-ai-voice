import os
import shutil
import subprocess
from urllib.parse import urlparse
from strands import tool

GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')

@tool(
    name="clone_github_repo",
    description=(
        "Parses a GitHub repository URL, clones the repository locally using a personal access token, "
        "checks out a branch, validates the repo, and returns the local path along with a success message."
    )
)
def clone_github_repo(github_url: str, base_branch: str = "main") -> dict:
    """
    Args:
        github_url (str): The GitHub repository URL (e.g., https://github.com/user/repo)
        base_branch (str, optional): Branch to checkout after cloning. Defaults to "main".

    Returns:
        dict: {
            "repo_path": str,      # Local path where the repo was cloned
            "project_name": str,   # Name of the repository
            "message": str         # Human-readable confirmation for agents
        }

    Raises:
        ValueError: If the URL is invalid or not in the expected format
        RuntimeError: If cloning fails
    """
    if not github_url or not isinstance(github_url, str):
        raise ValueError("Invalid input: github_url must be a non-empty string")
    if not GITHUB_PERSONAL_ACCESS_TOKEN:
        raise ValueError("Missing GITHUB_PERSONAL_ACCESS_TOKEN environment variable")

    # Parse GitHub URL
    github_url = github_url.rstrip("/")
    parsed = urlparse(github_url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) != 2:
        raise ValueError("Invalid GitHub URL format. Expected: https://github.com/user/repo")

    project_name = path_parts[-1]
    clone_url = f"{github_url}.git" if not github_url.endswith(".git") else github_url
    repo_path = f"./tmp/{project_name}"

    # Remove old repo if exists
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)

    # Clone repo with token
    remote_url_with_token = f"https://{GITHUB_PERSONAL_ACCESS_TOKEN}@{clone_url.split('https://')[1]}"
    try:
        subprocess.run(["git", "clone", remote_url_with_token, repo_path], check=True, text=True, capture_output=True)
        subprocess.run(["git", "checkout", base_branch], cwd=repo_path, check=True, text=True, capture_output=True)
        subprocess.run(["git", "pull", "origin", base_branch], cwd=repo_path, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {e.stderr.strip()}") from e

    # Validate repo
    if not os.path.exists(repo_path) or not any(os.scandir(repo_path)):
        raise RuntimeError(f"Repo exists at {repo_path}, but it is empty or missing")

    # Success message for agent
    message = f"✅ Repository '{project_name}' successfully cloned to '{repo_path}' and is ready for use."

    return {
        "repo_path": repo_path,
        "project_name": project_name,
        "message": message
    }
