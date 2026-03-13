"""Full-text search across PayloadsAllTheThings repository."""

import os
import re
from dataclasses import dataclass

from cli_anything.payloads.core.repository import _SKIP_DIRS


@dataclass
class SearchResult:
    """A single search match."""
    file_path: str
    category: str
    line_number: int
    line_content: str
    context_before: list[str]
    context_after: list[str]
    match_type: str  # "markdown", "intruder", "sample"

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "category": self.category,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "match_type": self.match_type,
        }


def search(repo_path: str, query: str, *,
           category: str | None = None,
           file_type: str | None = None,
           case_sensitive: bool = False,
           regex: bool = False,
           context_lines: int = 2,
           max_results: int = 100) -> list[SearchResult]:
    """Search across all files in the repository.

    Args:
        repo_path: Path to the repo root.
        query: Search string or regex pattern.
        category: Limit search to a specific category directory.
        file_type: Filter by type: "md", "txt", "all". Default: all searchable.
        case_sensitive: Whether to match case.
        regex: Whether query is a regex pattern.
        context_lines: Number of context lines before/after match.
        max_results: Maximum number of results to return.

    Returns:
        List of SearchResult objects.
    """
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    else:
        if not case_sensitive:
            query_lower = query.lower()

    results = []
    search_root = repo_path
    if category:
        search_root = os.path.join(repo_path, category)
        if not os.path.isdir(search_root):
            raise ValueError(f"Category directory not found: {category}")

    # Determine which extensions to search
    searchable_exts = {".md", ".txt"}
    if file_type == "md":
        searchable_exts = {".md"}
    elif file_type == "txt":
        searchable_exts = {".txt"}
    elif file_type == "all":
        searchable_exts = {
            ".md", ".txt", ".py", ".php", ".html", ".xml", ".yaml",
            ".yml", ".json", ".sh", ".rb", ".js", ".xsl", ".xslt",
            ".sql", ".jsp", ".asp", ".aspx",
        }

    for root, dirs, files in os.walk(search_root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith(".")]

        for fname in sorted(files):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in searchable_exts:
                continue

            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except (OSError, UnicodeDecodeError):
                continue

            # Determine category from path
            rel = os.path.relpath(root, repo_path)
            cat = rel.split(os.sep)[0] if rel != "." else ""

            # Determine match type
            if ext == ".md":
                match_type = "markdown"
            elif ext == ".txt":
                match_type = "intruder"
            else:
                match_type = "sample"

            for i, line in enumerate(lines):
                line_stripped = line.rstrip("\n\r")
                matched = False

                if regex:
                    matched = bool(pattern.search(line_stripped))
                elif case_sensitive:
                    matched = query in line_stripped
                else:
                    matched = query_lower in line_stripped.lower()

                if matched:
                    ctx_before = [
                        lines[j].rstrip("\n\r")
                        for j in range(max(0, i - context_lines), i)
                    ]
                    ctx_after = [
                        lines[j].rstrip("\n\r")
                        for j in range(i + 1, min(len(lines), i + 1 + context_lines))
                    ]
                    results.append(SearchResult(
                        file_path=os.path.relpath(fpath, repo_path),
                        category=cat,
                        line_number=i + 1,
                        line_content=line_stripped,
                        context_before=ctx_before,
                        context_after=ctx_after,
                        match_type=match_type,
                    ))
                    if len(results) >= max_results:
                        return results

    return results


def search_categories(repo_path: str, query: str) -> list[str]:
    """Search category names matching a query.

    Returns:
        List of matching category directory names.
    """
    query_lower = query.lower()
    categories = []
    for entry in sorted(os.listdir(repo_path)):
        full = os.path.join(repo_path, entry)
        if not os.path.isdir(full) or entry in _SKIP_DIRS or entry.startswith("."):
            continue
        if query_lower in entry.lower():
            categories.append(entry)
    return categories
