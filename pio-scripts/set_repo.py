Import('env')
import subprocess
import re

def get_github_repo():
    """Extract GitHub repository name from git remote URL."""
    try:
        # Get the remote URL for origin
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, check=True)
        remote_url = result.stdout.strip()
        
        # Check if it's a GitHub URL
        if 'github.com' not in remote_url.lower():
            return 'unknown'
        
        # Parse GitHub URL patterns:
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        # https://github.com/owner/repo
        
        # Remove .git suffix if present
        if remote_url.endswith('.git'):
            remote_url = remote_url[:-4]
        
        # Handle HTTPS URLs
        https_match = re.search(r'github\.com/([^/]+/[^/]+)', remote_url, re.IGNORECASE)
        if https_match:
            return https_match.group(1)
        
        # Handle SSH URLs
        ssh_match = re.search(r'github\.com:([^/]+/[^/]+)', remote_url, re.IGNORECASE)
        if ssh_match:
            return ssh_match.group(1)
        
        return 'unknown'
        
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        # Git command failed or git is not available
        return 'unknown'

repo = get_github_repo()
env.Append(BUILD_FLAGS=[f'-DWLED_REPO="{repo}"'])