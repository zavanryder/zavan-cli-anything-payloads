"""cli-anything-payloads: CLI harness for PayloadsAllTheThings.

Provides structured search, extraction, and export of security payloads
from the PayloadsAllTheThings repository.
"""

import json
import os
import sys

import click

from cli_anything.payloads.core.repository import (
    find_repo, list_categories, category_info, repo_stats, resolve_category,
)
from cli_anything.payloads.core.parser import (
    extract_code_blocks, extract_sections, read_intruder_file,
)
from cli_anything.payloads.core.search import search, search_categories
from cli_anything.payloads.core.export import (
    export_code_blocks, export_intruder, export_category_markdown,
)
from cli_anything.payloads.core.session import Session


def _resolve_repo(ctx) -> str:
    """Get the repo path from context."""
    return ctx.obj["repo_path"]


def _output(ctx, data, human_fn):
    """Output data as JSON or human-readable.

    Args:
        ctx: Click context.
        data: Dict/list data for JSON output.
        human_fn: Callable that prints human-readable output.
    """
    if ctx.obj.get("json_mode"):
        click.echo(json.dumps(data, indent=2))
    else:
        human_fn(data)


# ── Main group ────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--repo", envvar="PAYLOADS_REPO", default=None,
              help="Path to PayloadsAllTheThings repository.")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output in JSON format for machine consumption.")
@click.version_option(version="1.0.0", prog_name="cli-anything-payloads")
@click.pass_context
def cli(ctx, repo, json_mode):
    """CLI harness for PayloadsAllTheThings — search, extract, and export security payloads."""
    ctx.ensure_object(dict)
    ctx.obj["json_mode"] = json_mode

    # Resolve repo path
    repo_path = repo or os.environ.get("PAYLOADS_REPO")
    if repo_path:
        try:
            repo_path = find_repo(repo_path)
        except RuntimeError as e:
            click.echo(str(e), err=True)
            ctx.exit(1)
    ctx.obj["repo_path"] = repo_path

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── list ──────────────────────────────────────────────────────────────

@cli.command("list")
@click.option("--filter", "-f", "name_filter", default=None,
              help="Filter categories by name substring.")
@click.pass_context
def list_cmd(ctx, name_filter):
    """List all vulnerability categories."""
    repo = _resolve_repo(ctx)
    if not repo:
        click.echo("Error: --repo is required (or set PAYLOADS_REPO)", err=True)
        ctx.exit(1)

    cats = list_categories(repo)
    if name_filter:
        cats = [c for c in cats if name_filter.lower() in c["name"].lower()]

    data = {
        "categories": [
            {
                "name": c["name"],
                "md_files": len(c["md_files"]),
                "intruder_files": len(c["intruder_files"]),
                "has_intruder": c["has_intruder"],
                "has_files": c["has_files"],
            }
            for c in cats
        ],
        "total": len(cats),
    }

    def _human(d):
        click.echo(f"\n  Categories ({d['total']}):\n")
        for c in d["categories"]:
            flags = []
            if c["has_intruder"]:
                flags.append(f"intruder:{c['intruder_files']}")
            if c["has_files"]:
                flags.append("files")
            extra = f"  ({', '.join(flags)})" if flags else ""
            click.echo(f"    {c['name']}{extra}")
        click.echo()

    _output(ctx, data, _human)


# ── show ──────────────────────────────────────────────────────────────

@cli.command("show")
@click.argument("category")
@click.option("--file", "-f", "filename", default=None,
              help="Specific .md file within the category.")
@click.option("--sections", is_flag=True, default=False,
              help="Show only section headings (table of contents).")
@click.pass_context
def show_cmd(ctx, category, filename, sections):
    """Show documentation for a vulnerability category."""
    repo = _resolve_repo(ctx)
    if not repo:
        click.echo("Error: --repo is required", err=True)
        ctx.exit(1)

    try:
        cat_name = resolve_category(repo, category)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)

    cat_path = os.path.join(repo, cat_name)
    target = filename or "README.md"
    fpath = os.path.join(cat_path, target)

    if not os.path.isfile(fpath):
        available = [f for f in os.listdir(cat_path) if f.endswith(".md")]
        click.echo(f"Error: {target} not found. Available: {', '.join(available)}", err=True)
        ctx.exit(1)

    if sections:
        secs = extract_sections(fpath)
        data = {"category": cat_name, "file": target, "sections": secs}

        def _human(d):
            click.echo(f"\n  {d['category']} / {d['file']}  — Sections:\n")
            for s in d["sections"]:
                indent = "  " * s["level"]
                blocks = f" [{s['code_block_count']} blocks]" if s["code_block_count"] else ""
                click.echo(f"  {indent}{s['title']}{blocks}")
            click.echo()

        _output(ctx, data, _human)
    else:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if ctx.obj.get("json_mode"):
            blocks = extract_code_blocks(fpath)
            data = {
                "category": cat_name,
                "file": target,
                "content": content,
                "code_block_count": len(blocks),
                "languages": list(set(b.language for b in blocks if b.language)),
            }
            click.echo(json.dumps(data, indent=2))
        else:
            click.echo(content)


# ── info ──────────────────────────────────────────────────────────────

@cli.command("info")
@click.argument("category", required=False)
@click.pass_context
def info_cmd(ctx, category):
    """Show detailed info about a category or the whole repository."""
    repo = _resolve_repo(ctx)
    if not repo:
        click.echo("Error: --repo is required", err=True)
        ctx.exit(1)

    if category:
        try:
            data = category_info(repo, category)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)

        def _human(d):
            click.echo(f"\n  Category: {d['name']}")
            click.echo(f"  Path: {d['path']}")
            click.echo(f"  Markdown files: {len(d['md_files'])}")
            for f in d["md_files"]:
                click.echo(f"    - {f}")
            if d["intruder_files"]:
                click.echo(f"  Intruder wordlists: {len(d['intruder_files'])}")
                for f in d["intruder_files"]:
                    click.echo(f"    - {f}")
            if d["sample_files"]:
                click.echo(f"  Sample files: {len(d['sample_files'])}")
                for f in d["sample_files"]:
                    click.echo(f"    - {f}")
            click.echo()

        _output(ctx, data, _human)
    else:
        data = repo_stats(repo)

        def _human(d):
            click.echo(f"\n  PayloadsAllTheThings Repository")
            click.echo(f"  Path: {d['repo_path']}")
            click.echo(f"  Categories: {d['categories']}")
            click.echo(f"  Markdown files: {d['markdown_files']}")
            click.echo(f"  Intruder wordlists: {d['intruder_wordlists']}")
            click.echo(f"  Sample files: {d['sample_files']}")
            click.echo(f"  Categories with Intruder: {d['categories_with_intruder']}")
            click.echo()

        _output(ctx, data, _human)


# ── search ────────────────────────────────────────────────────────────

@cli.command("search")
@click.argument("query")
@click.option("--category", "-c", default=None, help="Limit to a specific category.")
@click.option("--type", "-t", "file_type", default=None,
              type=click.Choice(["md", "txt", "all"]),
              help="Filter by file type.")
@click.option("--regex", "-r", is_flag=True, default=False,
              help="Treat query as a regex pattern.")
@click.option("--case-sensitive", "-s", is_flag=True, default=False,
              help="Case-sensitive search.")
@click.option("--max-results", "-n", default=50, type=click.IntRange(min=1),
              help="Maximum results.")
@click.option("--context", "-C", "context_lines", default=1,
              type=click.IntRange(min=0), help="Context lines around matches.")
@click.pass_context
def search_cmd(ctx, query, category, file_type, regex, case_sensitive,
               max_results, context_lines):
    """Search across all payloads and documentation."""
    repo = _resolve_repo(ctx)
    if not repo:
        click.echo("Error: --repo is required", err=True)
        ctx.exit(1)

    if category:
        try:
            category = resolve_category(repo, category)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)

    try:
        results = search(repo, query, category=category, file_type=file_type,
                         regex=regex, case_sensitive=case_sensitive,
                         context_lines=context_lines, max_results=max_results)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)

    data = {
        "query": query,
        "result_count": len(results),
        "results": [r.to_dict() for r in results],
    }

    def _human(d):
        if not d["results"]:
            click.echo(f"\n  No results for '{query}'.\n")
            return
        click.echo(f"\n  Found {d['result_count']} matches for '{query}':\n")
        for r in d["results"]:
            click.echo(f"  {r['file_path']}:{r['line_number']}")
            for cl in r["context_before"]:
                click.echo(f"    {cl}")
            click.echo(f"  > {r['line_content']}")
            for cl in r["context_after"]:
                click.echo(f"    {cl}")
            click.echo()

    _output(ctx, data, _human)


# ── extract ───────────────────────────────────────────────────────────

@cli.command("extract")
@click.argument("category")
@click.option("--language", "-l", default=None,
              help="Filter code blocks by language (sql, bash, js, etc.).")
@click.option("--section", "-s", default=None,
              help="Filter by section title substring.")
@click.option("--file", "-f", "filename", default=None,
              help="Specific .md file within the category.")
@click.option("--index", "-i", "block_index", default=None, type=int,
              help="Extract a specific block by index (1-based).")
@click.pass_context
def extract_cmd(ctx, category, language, section, filename, block_index):
    """Extract code blocks from a category's documentation."""
    repo = _resolve_repo(ctx)
    if not repo:
        click.echo("Error: --repo is required", err=True)
        ctx.exit(1)

    try:
        cat_name = resolve_category(repo, category)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)

    cat_path = os.path.join(repo, cat_name)

    # Collect blocks
    all_blocks = []
    if filename:
        fpath = os.path.join(cat_path, filename)
        if not os.path.isfile(fpath):
            click.echo(f"Error: {filename} not found in {cat_name}", err=True)
            ctx.exit(1)
        all_blocks = extract_code_blocks(fpath, language=language,
                                         section_filter=section)
    else:
        for fname in sorted(os.listdir(cat_path)):
            if fname.endswith(".md"):
                fpath = os.path.join(cat_path, fname)
                all_blocks.extend(
                    extract_code_blocks(fpath, language=language,
                                        section_filter=section)
                )

    if block_index is not None:
        if block_index < 1 or block_index > len(all_blocks):
            click.echo(f"Error: Block index {block_index} out of range (1-{len(all_blocks)})", err=True)
            ctx.exit(1)
        all_blocks = [all_blocks[block_index - 1]]

    data = {
        "category": cat_name,
        "language_filter": language,
        "section_filter": section,
        "block_count": len(all_blocks),
        "blocks": [b.to_dict() for b in all_blocks],
    }

    def _human(d):
        if not d["blocks"]:
            click.echo(f"\n  No code blocks found.\n")
            return
        click.echo(f"\n  {d['block_count']} code blocks from '{d['category']}':\n")
        for i, b in enumerate(d["blocks"], 1):
            lang = f" [{b['language']}]" if b["language"] else ""
            click.echo(f"  --- Block {i}{lang} (section: {b['section']}) ---")
            click.echo(b["content"])
            click.echo()

    _output(ctx, data, _human)


# ── intruder ──────────────────────────────────────────────────────────

@cli.command("intruder")
@click.argument("category")
@click.option("--file", "-f", "filename", default=None,
              help="Specific wordlist file.")
@click.option("--head", "-n", "head_count", default=None, type=int,
              help="Show only first N payloads.")
@click.pass_context
def intruder_cmd(ctx, category, filename, head_count):
    """List or display intruder wordlists for a category."""
    repo = _resolve_repo(ctx)
    if not repo:
        click.echo("Error: --repo is required", err=True)
        ctx.exit(1)

    try:
        cat_name = resolve_category(repo, category)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)

    intruder_dir = os.path.join(repo, cat_name, "Intruder")
    if not os.path.isdir(intruder_dir):
        click.echo(f"Error: No Intruder directory in '{cat_name}'", err=True)
        ctx.exit(1)

    if filename:
        fpath = os.path.join(intruder_dir, filename)
        if not os.path.isfile(fpath):
            available = [f for f in os.listdir(intruder_dir)
                         if os.path.isfile(os.path.join(intruder_dir, f))]
            click.echo(f"Error: File not found: {filename}", err=True)
            click.echo(f"Available: {', '.join(available)}", err=True)
            ctx.exit(1)

        payloads = read_intruder_file(fpath)
        if head_count:
            payloads = payloads[:head_count]

        data = {
            "category": cat_name,
            "file": filename,
            "payload_count": len(payloads),
            "payloads": payloads,
        }

        def _human(d):
            click.echo(f"\n  {d['file']} ({d['payload_count']} payloads):\n")
            for p in d["payloads"]:
                click.echo(p)
            click.echo()

        _output(ctx, data, _human)
    else:
        # List available intruder files
        files = []
        for f in sorted(os.listdir(intruder_dir)):
            fpath = os.path.join(intruder_dir, f)
            if os.path.isfile(fpath):
                payloads = read_intruder_file(fpath)
                files.append({
                    "name": f,
                    "payload_count": len(payloads),
                    "size": os.path.getsize(fpath),
                })

        data = {"category": cat_name, "files": files, "total": len(files)}

        def _human(d):
            click.echo(f"\n  Intruder wordlists for '{d['category']}' ({d['total']} files):\n")
            for f in d["files"]:
                click.echo(f"    {f['name']}  ({f['payload_count']} payloads)")
            click.echo()

        _output(ctx, data, _human)


# ── export ────────────────────────────────────────────────────────────

@cli.group("export")
@click.pass_context
def export_group(ctx):
    """Export payloads to files."""
    pass


@export_group.command("blocks")
@click.argument("category")
@click.argument("output")
@click.option("--language", "-l", default=None, help="Filter by language.")
@click.option("--section", "-s", default=None, help="Filter by section.")
@click.option("--format", "-F", "fmt", default="raw",
              type=click.Choice(["raw", "json", "numbered"]),
              help="Output format.")
@click.option("--overwrite", is_flag=True, default=False)
@click.pass_context
def export_blocks_cmd(ctx, category, output, language, section, fmt, overwrite):
    """Export code blocks from a category to a file."""
    repo = _resolve_repo(ctx)
    if not repo:
        click.echo("Error: --repo is required", err=True)
        ctx.exit(1)

    try:
        result = export_code_blocks(repo, category, output,
                                     language=language, section=section,
                                     format=fmt, overwrite=overwrite)
    except (ValueError, FileExistsError) as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)

    def _human(d):
        click.echo(f"\n  Exported {d['block_count']} code blocks from '{d['category']}'")
        click.echo(f"  Output: {d['output']} ({d['file_size']:,} bytes)")
        if d["languages"]:
            click.echo(f"  Languages: {', '.join(d['languages'])}")
        click.echo()

    _output(ctx, result, _human)


@export_group.command("intruder")
@click.argument("category")
@click.argument("output")
@click.option("--file", "-f", "filename", default=None,
              help="Specific wordlist file. Default: merge all.")
@click.option("--deduplicate", "-d", is_flag=True, default=False,
              help="Remove duplicate payloads.")
@click.option("--overwrite", is_flag=True, default=False)
@click.pass_context
def export_intruder_cmd(ctx, category, output, filename, deduplicate, overwrite):
    """Export intruder wordlists to a file."""
    repo = _resolve_repo(ctx)
    if not repo:
        click.echo("Error: --repo is required", err=True)
        ctx.exit(1)

    try:
        result = export_intruder(repo, category, output,
                                  filename=filename, overwrite=overwrite,
                                  deduplicate=deduplicate)
    except (ValueError, FileExistsError) as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)

    def _human(d):
        click.echo(f"\n  Exported {d['payload_count']} payloads from '{d['category']}'")
        if d["deduplicated"] and d["original_count"] != d["payload_count"]:
            click.echo(f"  Deduplicated: {d['original_count']} -> {d['payload_count']}")
        click.echo(f"  Output: {d['output']} ({d['file_size']:,} bytes)")
        click.echo()

    _output(ctx, result, _human)


@export_group.command("markdown")
@click.argument("category")
@click.argument("output")
@click.option("--overwrite", is_flag=True, default=False)
@click.pass_context
def export_markdown_cmd(ctx, category, output, overwrite):
    """Export all markdown from a category into a single file."""
    repo = _resolve_repo(ctx)
    if not repo:
        click.echo("Error: --repo is required", err=True)
        ctx.exit(1)

    try:
        result = export_category_markdown(repo, category, output, overwrite=overwrite)
    except (ValueError, FileExistsError) as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)

    def _human(d):
        click.echo(f"\n  Exported markdown from '{d['category']}'")
        click.echo(f"  Files: {', '.join(d['source_files'])}")
        click.echo(f"  Output: {d['output']} ({d['file_size']:,} bytes)")
        click.echo()

    _output(ctx, result, _human)


# ── session ───────────────────────────────────────────────────────────

@cli.group("session")
@click.pass_context
def session_group(ctx):
    """Manage session state (favorites, history)."""
    pass


@session_group.command("status")
@click.pass_context
def session_status(ctx):
    """Show current session state."""
    session = Session()
    data = session.to_dict()

    def _human(d):
        click.echo(f"\n  Session:")
        click.echo(f"  Current category: {d['current_category'] or '(none)'}")
        click.echo(f"  Favorites: {len(d['favorites'])}")
        if d["favorites"]:
            for f in d["favorites"]:
                click.echo(f"    - {f}")
        click.echo(f"  Search history: {len(d['search_history'])} entries")
        click.echo()

    _output(ctx, data, _human)


@session_group.command("clear")
@click.pass_context
def session_clear(ctx):
    """Clear all session state."""
    session = Session()
    session.clear()

    data = {"status": "cleared"}

    def _human(d):
        click.echo("  Session cleared.")

    _output(ctx, data, _human)


@session_group.command("favorite")
@click.argument("category")
@click.option("--remove", is_flag=True, default=False, help="Remove from favorites.")
@click.pass_context
def session_favorite(ctx, category, remove):
    """Add or remove a category from favorites."""
    repo = _resolve_repo(ctx)
    if repo:
        try:
            category = resolve_category(repo, category)
        except ValueError:
            click.echo(f"Warning: '{category}' could not be resolved to a known category", err=True)

    session = Session()
    if remove:
        session.remove_favorite(category)
        action = "removed"
    else:
        session.add_favorite(category)
        action = "added"

    data = {"category": category, "action": action, "favorites": session.favorites}

    def _human(d):
        click.echo(f"  {d['action'].title()}: {d['category']}")

    _output(ctx, data, _human)


# ── REPL ──────────────────────────────────────────────────────────────

class _ReplState:
    """Mutable state shared across REPL command handlers."""

    def __init__(self, ctx, skin, session):
        self.ctx = ctx
        self.skin = skin
        self.session = session

    @property
    def repo(self):
        return self.ctx.obj.get("repo_path")

    @repo.setter
    def repo(self, value):
        self.ctx.obj["repo_path"] = value

    def require_repo(self) -> str | None:
        if not self.repo:
            self.skin.error("No repository set")
            return None
        return self.repo

    def resolve_target(self, args) -> str | None:
        return " ".join(args) if args else self.session.current_category


def _repl_set_repo(state, args):
    if not args:
        state.skin.error("Usage: set-repo <path>")
        return
    try:
        state.repo = find_repo(args[0])
        state.skin.success(f"Repository: {state.repo}")
    except RuntimeError as e:
        state.skin.error(str(e))


def _repl_cd(state, args):
    if not args:
        state.session.current_category = None
        state.skin.info("Cleared current category")
        return
    repo = state.require_repo()
    if not repo:
        return
    try:
        cat_name = resolve_category(repo, " ".join(args))
        state.session.current_category = cat_name
        state.skin.success(f"Category: {cat_name}")
    except ValueError as e:
        state.skin.error(str(e))


def _repl_list(state, args):
    repo = state.require_repo()
    if not repo:
        return
    cats = list_categories(repo)
    name_filter = " ".join(args) if args else None
    if name_filter:
        cats = [c for c in cats if name_filter.lower() in c["name"].lower()]
    state.skin.table(
        ["Category", "MD Files", "Intruder", "Files"],
        [[c["name"], str(len(c["md_files"])),
          str(len(c["intruder_files"])) if c["has_intruder"] else "-",
          "yes" if c["has_files"] else "-"] for c in cats],
    )


def _repl_show(state, args):
    repo = state.require_repo()
    if not repo:
        return
    target = state.resolve_target(args)
    if not target:
        state.skin.error("Usage: show <category>")
        return
    try:
        cat_name = resolve_category(repo, target)
        secs = extract_sections(os.path.join(repo, cat_name, "README.md"))
        state.skin.section(cat_name)
        for s in secs:
            indent = "  " * (s["level"] - 1)
            blocks = f" [{s['code_block_count']}]" if s["code_block_count"] else ""
            click.echo(f"  {indent}{s['title']}{blocks}")
    except (ValueError, FileNotFoundError) as e:
        state.skin.error(str(e))


def _repl_info(state, args):
    repo = state.require_repo()
    if not repo:
        return
    target = state.resolve_target(args)
    if target:
        try:
            info = category_info(repo, target)
            state.skin.status_block({
                "Category": info["name"],
                "MD files": str(len(info["md_files"])),
                "Intruder": str(len(info["intruder_files"])),
                "Samples": str(len(info["sample_files"])),
                "Images": str(len(info["image_files"])),
            })
        except ValueError as e:
            state.skin.error(str(e))
    else:
        stats = repo_stats(repo)
        state.skin.status_block({
            "Categories": str(stats["categories"]),
            "Markdown files": str(stats["markdown_files"]),
            "Intruder wordlists": str(stats["intruder_wordlists"]),
            "Sample files": str(stats["sample_files"]),
        })


def _repl_search(state, args):
    repo = state.require_repo()
    if not repo:
        return
    if not args:
        state.skin.error("Usage: search <query>")
        return
    query = " ".join(args)
    state.session.add_search(query)
    cat_filter = state.session.current_category
    results = search(repo, query, category=cat_filter, max_results=20)
    if not results:
        state.skin.warning(f"No results for '{query}'")
    else:
        state.skin.info(f"{len(results)} matches for '{query}'")
        for r in results:
            click.echo(f"    {r.file_path}:{r.line_number}")
            click.echo(f"      {r.line_content[:120]}")


def _repl_extract(state, args):
    repo = state.require_repo()
    if not repo:
        return
    target = state.resolve_target(args)
    if not target:
        state.skin.error("Usage: extract <category>")
        return
    try:
        cat_name = resolve_category(repo, target)
    except ValueError as e:
        state.skin.error(str(e))
        return

    cat_path = os.path.join(repo, cat_name)
    blocks = []
    for fname in sorted(os.listdir(cat_path)):
        if fname.endswith(".md"):
            blocks.extend(extract_code_blocks(os.path.join(cat_path, fname)))

    if not blocks:
        state.skin.warning("No code blocks found")
        return

    state.skin.info(f"{len(blocks)} code blocks")
    langs = {}
    for b in blocks:
        lang = b.language or "(none)"
        langs[lang] = langs.get(lang, 0) + 1
    for lang, count in sorted(langs.items()):
        state.skin.status(lang, str(count))
    click.echo()
    for i, b in enumerate(blocks[:10], 1):
        lang_tag = f" [{b.language}]" if b.language else ""
        click.echo(f"  --- {i}{lang_tag} ({b.section}) ---")
        for ln in b.content.split("\n")[:3]:
            click.echo(f"    {ln}")
        if b.content.count("\n") > 3:
            click.echo("    ...")
    if len(blocks) > 10:
        state.skin.hint(f"  ... and {len(blocks) - 10} more")


def _repl_intruder(state, args):
    repo = state.require_repo()
    if not repo:
        return
    target = state.resolve_target(args)
    if not target:
        state.skin.error("Usage: intruder <category>")
        return
    try:
        cat_name = resolve_category(repo, target)
        intruder_dir = os.path.join(repo, cat_name, "Intruder")
        if not os.path.isdir(intruder_dir):
            state.skin.warning(f"No Intruder directory in '{cat_name}'")
            return
        for f in sorted(os.listdir(intruder_dir)):
            fpath = os.path.join(intruder_dir, f)
            if os.path.isfile(fpath):
                count = len(read_intruder_file(fpath))
                state.skin.status(f, f"{count} payloads")
    except ValueError as e:
        state.skin.error(str(e))


def _repl_favorites(state, args):
    favs = state.session.favorites
    if not favs:
        state.skin.info("No favorites yet. Use: fav <category>")
    else:
        state.skin.section("Favorites")
        for f in favs:
            click.echo(f"    {f}")


def _repl_fav(state, args):
    if not args:
        state.skin.error("Usage: fav <category>")
        return
    cat_name = " ".join(args)
    if state.repo:
        try:
            cat_name = resolve_category(state.repo, cat_name)
        except ValueError:
            pass
    if cat_name in state.session.favorites:
        state.session.remove_favorite(cat_name)
        state.skin.info(f"Removed: {cat_name}")
    else:
        state.session.add_favorite(cat_name)
        state.skin.success(f"Added: {cat_name}")


def _repl_export(state, args):
    state.skin.info("Export subcommands: blocks, intruder, markdown")
    state.skin.hint("Use CLI mode: cli-anything-payloads export blocks <cat> <out>")


_REPL_DISPATCH = {
    "set-repo": _repl_set_repo,
    "cd": _repl_cd,
    "list": _repl_list,
    "show": _repl_show,
    "info": _repl_info,
    "search": _repl_search,
    "extract": _repl_extract,
    "intruder": _repl_intruder,
    "favorites": _repl_favorites,
    "fav": _repl_fav,
    "export": _repl_export,
}


@cli.command("repl", hidden=True)
@click.pass_context
def repl(ctx):
    """Interactive REPL mode."""
    from cli_anything.payloads.utils.repl_skin import ReplSkin

    skin = ReplSkin("payloads", version="1.0.0")
    skin.print_banner()

    repo = ctx.obj.get("repo_path")
    if not repo:
        skin.warning("No repository set. Use: set-repo <path>")
    else:
        skin.success(f"Repository: {repo}")

    session = Session()
    pt_session = skin.create_prompt_session()
    state = _ReplState(ctx, skin, session)

    help_commands = {
        "list": "List vulnerability categories",
        "show <category>": "Show category documentation",
        "info [category]": "Show category or repo info",
        "search <query>": "Search across all payloads",
        "extract <category>": "Extract code blocks",
        "intruder <category>": "List/show intruder wordlists",
        "export blocks <cat> <out>": "Export code blocks to file",
        "export intruder <cat> <out>": "Export wordlists to file",
        "export markdown <cat> <out>": "Export markdown to file",
        "cd <category>": "Set current category",
        "set-repo <path>": "Set repository path",
        "favorites": "Show favorite categories",
        "fav <category>": "Toggle favorite",
        "help": "Show this help",
        "quit": "Exit",
    }

    while True:
        try:
            cat_ctx = session.current_category or ""
            line = skin.get_input(pt_session, context=cat_ctx)
            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()
            args = parts[1:]

            session.add_command(line)

            if cmd in ("quit", "exit", "q"):
                skin.print_goodbye()
                break
            elif cmd == "help":
                skin.help(help_commands)
            elif cmd in _REPL_DISPATCH:
                _REPL_DISPATCH[cmd](state, args)
            else:
                skin.warning(f"Unknown command: {cmd}. Type 'help' for commands.")

        except KeyboardInterrupt:
            click.echo()
            continue
        except EOFError:
            skin.print_goodbye()
            break


def main():
    cli(auto_envvar_prefix="PAYLOADS")


if __name__ == "__main__":
    main()
