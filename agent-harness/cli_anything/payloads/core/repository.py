"""Repository discovery and indexing for PayloadsAllTheThings."""

import os
import json
from pathlib import Path


# Directories that are not vulnerability categories
_SKIP_DIRS = {
    ".git", ".github", "_template_vuln", "_LEARNING_AND_SOCIALS",
    "node_modules", "__pycache__", ".venv",
}

# Root-level files that are not categories
_SKIP_FILES = {
    "README.md", "CONTRIBUTING.md", "DISCLAIMER.md", "LICENSE",
    "mkdocs.yml", "custom.css", ".gitignore",
}


def find_repo(path: str | None = None) -> str:
    """Find and validate a PayloadsAllTheThings repository.

    Args:
        path: Explicit path to the repo root. If None, checks common locations.

    Returns:
        Absolute path to the repo root.

    Raises:
        RuntimeError: If the repository cannot be found.
    """
    if path:
        p = os.path.abspath(os.path.expanduser(path))
        if _is_repo(p):
            return p
        # Maybe they pointed at the parent
        sub = os.path.join(p, "PayloadsAllTheThings")
        if _is_repo(sub):
            return sub
        raise RuntimeError(
            f"Not a valid PayloadsAllTheThings repo: {p}\n"
            "Expected directories like 'SQL Injection', 'XSS Injection', etc.\n"
            "Clone with: git clone https://github.com/swisskyrepo/PayloadsAllTheThings.git"
        )
    raise RuntimeError(
        "No repository path provided.\n"
        "Use --repo <path> or set PAYLOADS_REPO environment variable.\n"
        "Clone with: git clone https://github.com/swisskyrepo/PayloadsAllTheThings.git"
    )


def _is_repo(path: str) -> bool:
    """Check if a path looks like a PayloadsAllTheThings checkout."""
    if not os.path.isdir(path):
        return False
    # Check for at least a few known category directories
    markers = ["SQL Injection", "XSS Injection", "Command Injection"]
    return sum(1 for m in markers if os.path.isdir(os.path.join(path, m))) >= 2


def list_categories(repo_path: str) -> list[dict]:
    """List all vulnerability categories in the repository.

    Returns:
        List of dicts with keys: name, path, file_count, has_intruder, has_files.
    """
    categories = []
    for entry in sorted(os.listdir(repo_path)):
        full = os.path.join(repo_path, entry)
        if not os.path.isdir(full):
            continue
        if entry in _SKIP_DIRS or entry.startswith("."):
            continue
        cat = {
            "name": entry,
            "path": full,
            "has_readme": os.path.isfile(os.path.join(full, "README.md")),
            "has_intruder": os.path.isdir(os.path.join(full, "Intruder")),
            "has_files": os.path.isdir(os.path.join(full, "Files")),
        }
        # Count markdown files
        cat["md_files"] = [
            f for f in os.listdir(full)
            if f.endswith(".md") and os.path.isfile(os.path.join(full, f))
        ]
        # Count intruder wordlists
        intruder_dir = os.path.join(full, "Intruder")
        if cat["has_intruder"]:
            cat["intruder_files"] = [
                f for f in os.listdir(intruder_dir)
                if os.path.isfile(os.path.join(intruder_dir, f))
            ]
        else:
            cat["intruder_files"] = []
        categories.append(cat)
    return categories


def category_info(repo_path: str, category_name: str) -> dict:
    """Get detailed information about a specific category.

    Args:
        repo_path: Path to the repo root.
        category_name: Category directory name (fuzzy-matched).

    Returns:
        Dict with full category information.

    Raises:
        ValueError: If category not found.
    """
    match = resolve_category(repo_path, category_name)
    cat_path = os.path.join(repo_path, match)

    info = {
        "name": match,
        "path": cat_path,
        "md_files": [],
        "intruder_files": [],
        "sample_files": [],
        "image_files": [],
    }

    for root, dirs, files in os.walk(cat_path):
        rel = os.path.relpath(root, cat_path)
        for f in files:
            fpath = os.path.join(root, f)
            frel = os.path.join(rel, f) if rel != "." else f
            ext = os.path.splitext(f)[1].lower()
            if ext == ".md":
                info["md_files"].append(frel)
            elif ext == ".txt":
                info["intruder_files"].append(frel)
            elif ext in (".png", ".jpg", ".jpeg", ".gif", ".svg"):
                info["image_files"].append(frel)
            else:
                info["sample_files"].append(frel)

    return info


def resolve_category(repo_path: str, name: str) -> str:
    """Fuzzy-match a category name to an actual directory.

    Tries exact match first, then case-insensitive, then substring.

    Returns:
        The actual directory name.

    Raises:
        ValueError: If no match found.
    """
    entries = [
        e for e in os.listdir(repo_path)
        if os.path.isdir(os.path.join(repo_path, e)) and e not in _SKIP_DIRS
    ]

    # Exact match
    if name in entries:
        return name

    # Case-insensitive exact match
    lower = name.lower()
    for e in entries:
        if e.lower() == lower:
            return e

    # Substring match
    matches = [e for e in entries if lower in e.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous category '{name}'. Matches: {', '.join(sorted(matches))}"
        )

    # Word-based fuzzy: split on spaces and match all words
    words = lower.split()
    fuzzy = [
        e for e in entries
        if all(w in e.lower() for w in words)
    ]
    if len(fuzzy) == 1:
        return fuzzy[0]
    if len(fuzzy) > 1:
        raise ValueError(
            f"Ambiguous category '{name}'. Matches: {', '.join(sorted(fuzzy))}"
        )

    raise ValueError(
        f"Category not found: '{name}'. Use 'list' to see all categories."
    )


def repo_stats(repo_path: str) -> dict:
    """Get overall repository statistics."""
    cats = list_categories(repo_path)
    total_md = 0
    total_intruder = 0
    total_samples = 0
    total_images = 0

    for root, dirs, files in os.walk(repo_path):
        # Skip hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext == ".md":
                total_md += 1
            elif ext == ".txt":
                total_intruder += 1
            elif ext in (".png", ".jpg", ".jpeg", ".gif", ".svg"):
                total_images += 1
            elif ext not in ("", ".css", ".yml"):
                total_samples += 1

    return {
        "repo_path": repo_path,
        "categories": len(cats),
        "markdown_files": total_md,
        "intruder_wordlists": total_intruder,
        "sample_files": total_samples,
        "image_files": total_images,
        "categories_with_intruder": sum(1 for c in cats if c["has_intruder"]),
        "categories_with_files": sum(1 for c in cats if c["has_files"]),
    }
