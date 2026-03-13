"""Export payloads to files in various formats."""

import json
import os
from pathlib import Path

from cli_anything.payloads.core.parser import (
    extract_code_blocks,
    read_intruder_file,
    CodeBlock,
)
from cli_anything.payloads.core.repository import resolve_category


def export_code_blocks(repo_path: str, category: str, output_path: str, *,
                       language: str | None = None,
                       section: str | None = None,
                       format: str = "raw",
                       overwrite: bool = False) -> dict:
    """Export extracted code blocks from a category to a file.

    Args:
        repo_path: Repository root path.
        category: Category name (fuzzy-matched).
        output_path: Output file path.
        language: Filter by language tag.
        section: Filter by section title.
        format: Output format: "raw", "json", "numbered".
        overwrite: Whether to overwrite existing files.

    Returns:
        Dict with export metadata.
    """
    cat_name = resolve_category(repo_path, category)
    cat_path = os.path.join(repo_path, cat_name)

    # Collect blocks from all .md files in the category
    all_blocks: list[CodeBlock] = []
    for fname in sorted(os.listdir(cat_path)):
        if fname.endswith(".md"):
            fpath = os.path.join(cat_path, fname)
            blocks = extract_code_blocks(fpath, language=language,
                                         section_filter=section)
            all_blocks.extend(blocks)

    if not all_blocks:
        raise ValueError(
            f"No code blocks found in '{cat_name}'"
            + (f" with language='{language}'" if language else "")
            + (f" in section='{section}'" if section else "")
        )

    output_path = os.path.abspath(output_path)
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(f"Output file exists: {output_path}. Use --overwrite.")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if format == "json":
        data = {
            "category": cat_name,
            "language_filter": language,
            "section_filter": section,
            "block_count": len(all_blocks),
            "blocks": [b.to_dict() for b in all_blocks],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    elif format == "numbered":
        with open(output_path, "w", encoding="utf-8") as f:
            for i, block in enumerate(all_blocks, 1):
                lang = f" [{block.language}]" if block.language else ""
                f.write(f"# --- Block {i}{lang} (section: {block.section}) ---\n")
                f.write(block.content)
                f.write("\n\n")
    else:  # raw
        with open(output_path, "w", encoding="utf-8") as f:
            for block in all_blocks:
                f.write(block.content)
                f.write("\n\n")

    file_size = os.path.getsize(output_path)
    return {
        "output": output_path,
        "category": cat_name,
        "block_count": len(all_blocks),
        "format": format,
        "file_size": file_size,
        "languages": list(set(b.language for b in all_blocks if b.language)),
    }


def export_intruder(repo_path: str, category: str, output_path: str, *,
                    filename: str | None = None,
                    overwrite: bool = False,
                    deduplicate: bool = False) -> dict:
    """Export intruder wordlists from a category.

    Args:
        repo_path: Repository root path.
        category: Category name.
        output_path: Output file path.
        filename: Specific intruder file to export. None = merge all.
        overwrite: Whether to overwrite existing files.
        deduplicate: Remove duplicate lines.

    Returns:
        Dict with export metadata.
    """
    cat_name = resolve_category(repo_path, category)
    intruder_dir = os.path.join(repo_path, cat_name, "Intruder")

    if not os.path.isdir(intruder_dir):
        raise ValueError(f"No Intruder directory in '{cat_name}'")

    payloads: list[str] = []
    source_files = []

    if filename:
        fpath = os.path.join(intruder_dir, filename)
        if not os.path.isfile(fpath):
            available = [f for f in os.listdir(intruder_dir)
                         if os.path.isfile(os.path.join(intruder_dir, f))]
            raise ValueError(
                f"File not found: {filename}\n"
                f"Available: {', '.join(available)}"
            )
        payloads = read_intruder_file(fpath)
        source_files = [filename]
    else:
        for f in sorted(os.listdir(intruder_dir)):
            fpath = os.path.join(intruder_dir, f)
            if os.path.isfile(fpath):
                payloads.extend(read_intruder_file(fpath))
                source_files.append(f)

    if not payloads:
        raise ValueError(f"No payloads found in '{cat_name}/Intruder/'")

    original_count = len(payloads)
    if deduplicate:
        seen = set()
        unique = []
        for p in payloads:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        payloads = unique

    output_path = os.path.abspath(output_path)
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(f"Output file exists: {output_path}. Use --overwrite.")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for p in payloads:
            f.write(p + "\n")

    return {
        "output": output_path,
        "category": cat_name,
        "source_files": source_files,
        "payload_count": len(payloads),
        "original_count": original_count,
        "deduplicated": deduplicate,
        "file_size": os.path.getsize(output_path),
    }


def export_category_markdown(repo_path: str, category: str, output_path: str, *,
                             overwrite: bool = False) -> dict:
    """Export all markdown content from a category into a single file.

    Returns:
        Dict with export metadata.
    """
    cat_name = resolve_category(repo_path, category)
    cat_path = os.path.join(repo_path, cat_name)

    md_files = sorted(
        f for f in os.listdir(cat_path)
        if f.endswith(".md") and os.path.isfile(os.path.join(cat_path, f))
    )
    if not md_files:
        raise ValueError(f"No markdown files in '{cat_name}'")

    output_path = os.path.abspath(output_path)
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(f"Output file exists: {output_path}. Use --overwrite.")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as out:
        for fname in md_files:
            fpath = os.path.join(cat_path, fname)
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if len(md_files) > 1:
                out.write(f"\n\n{'='*60}\n")
                out.write(f"# Source: {fname}\n")
                out.write(f"{'='*60}\n\n")
            out.write(content)

    return {
        "output": output_path,
        "category": cat_name,
        "source_files": md_files,
        "file_size": os.path.getsize(output_path),
    }
