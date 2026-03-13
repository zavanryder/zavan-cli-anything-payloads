"""Backend: locates and validates the PayloadsAllTheThings repository.

The repository is the hard dependency for this CLI — it's useless without it.
"""

import os
import shutil
import subprocess


def find_repo_from_env() -> str | None:
    """Check environment variable for repo path."""
    path = os.environ.get("PAYLOADS_REPO")
    if path and os.path.isdir(path):
        return os.path.abspath(path)
    return None


def clone_repo(target_dir: str | None = None) -> str:
    """Clone PayloadsAllTheThings if git is available.

    Args:
        target_dir: Where to clone. Defaults to ~/PayloadsAllTheThings.

    Returns:
        Path to the cloned repo.

    Raises:
        RuntimeError: If git is not installed or clone fails.
    """
    git = shutil.which("git")
    if not git:
        raise RuntimeError(
            "git is not installed. Install it with:\n"
            "  apt install git       # Debian/Ubuntu\n"
            "  brew install git      # macOS"
        )

    if target_dir is None:
        target_dir = os.path.expanduser("~/PayloadsAllTheThings")

    if os.path.isdir(target_dir):
        return target_dir

    result = subprocess.run(
        [git, "clone", "--depth=1",
         "https://github.com/swisskyrepo/PayloadsAllTheThings.git",
         target_dir],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to clone repository:\n{result.stderr}")

    return target_dir


def validate_repo(path: str) -> dict:
    """Validate a repository checkout and return basic info.

    Returns:
        Dict with repo metadata.

    Raises:
        RuntimeError: If the path is not a valid repo.
    """
    if not os.path.isdir(path):
        raise RuntimeError(
            f"PayloadsAllTheThings not found at: {path}\n"
            "Clone with: git clone https://github.com/swisskyrepo/PayloadsAllTheThings.git"
        )

    # Check for marker directories
    markers = ["SQL Injection", "XSS Injection", "Command Injection"]
    found = [m for m in markers if os.path.isdir(os.path.join(path, m))]
    if len(found) < 2:
        raise RuntimeError(
            f"Path does not appear to be PayloadsAllTheThings: {path}\n"
            "Expected category directories like 'SQL Injection', 'XSS Injection', etc."
        )

    # Check git info
    git_dir = os.path.join(path, ".git")
    has_git = os.path.isdir(git_dir)

    return {
        "path": os.path.abspath(path),
        "has_git": has_git,
        "marker_categories_found": found,
    }
