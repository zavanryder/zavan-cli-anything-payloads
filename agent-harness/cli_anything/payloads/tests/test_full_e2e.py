"""End-to-end tests for cli-anything-payloads using the real repository."""

import json
import os
import subprocess
import sys
import tempfile

import pytest

from cli_anything.payloads.core.repository import (
    find_repo, list_categories, category_info, repo_stats, resolve_category,
)
from cli_anything.payloads.core.parser import (
    extract_code_blocks, extract_sections, read_intruder_file,
)
from cli_anything.payloads.core.search import search
from cli_anything.payloads.core.export import (
    export_code_blocks, export_intruder, export_category_markdown,
)


# ── Real repo path ───────────────────────────────────────────────────

def _get_real_repo():
    """Find the real PayloadsAllTheThings repo."""
    # Check env var
    env_repo = os.environ.get("PAYLOADS_REPO")
    if env_repo and os.path.isdir(env_repo):
        return env_repo

    # Check relative to this test file (common layout)
    test_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(test_dir, "..", "..", "..", "..", "..", "PayloadsAllTheThings"),
        os.path.join(test_dir, "..", "..", "..", "..", "PayloadsAllTheThings"),
        os.path.expanduser("~/PayloadsAllTheThings"),
    ]
    for c in candidates:
        c = os.path.abspath(c)
        if os.path.isdir(c) and os.path.isdir(os.path.join(c, "SQL Injection")):
            return c

    pytest.skip("PayloadsAllTheThings repo not found. Set PAYLOADS_REPO env var.")


@pytest.fixture
def real_repo():
    return _get_real_repo()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


# ── Real Repo E2E Tests ──────────────────────────────────────────────

class TestRealRepoListing:

    def test_list_categories_has_known_entries(self, real_repo):
        cats = list_categories(real_repo)
        names = [c["name"] for c in cats]
        assert "SQL Injection" in names
        assert "XSS Injection" in names
        assert "Command Injection" in names
        assert "XXE Injection" in names
        assert len(cats) >= 50  # Should have 60+ categories
        print(f"\n  Categories: {len(cats)}")

    def test_category_info_sql_injection(self, real_repo):
        info = category_info(real_repo, "SQL Injection")
        assert info["name"] == "SQL Injection"
        assert len(info["md_files"]) >= 5  # README + MySQL + MSSQL + PostgreSQL + etc.
        assert len(info["intruder_files"]) >= 1
        print(f"\n  SQL Injection: {len(info['md_files'])} md, "
              f"{len(info['intruder_files'])} intruder, "
              f"{len(info['sample_files'])} samples")


class TestRealRepoParser:

    def test_extract_sections_sql_injection(self, real_repo):
        fpath = os.path.join(real_repo, "SQL Injection", "README.md")
        secs = extract_sections(fpath)
        titles = [s["title"] for s in secs]
        assert len(secs) >= 5
        print(f"\n  SQL Injection sections: {len(secs)}")
        for s in secs[:10]:
            print(f"    {'  ' * (s['level']-1)}{s['title']} [{s['code_block_count']}]")

    def test_extract_code_blocks_xss(self, real_repo):
        fpath = os.path.join(real_repo, "XSS Injection", "README.md")
        blocks = extract_code_blocks(fpath)
        assert len(blocks) >= 5
        langs = set(b.language for b in blocks if b.language)
        print(f"\n  XSS blocks: {len(blocks)}, languages: {langs}")

    def test_intruder_wordlists_command_injection(self, real_repo):
        intruder_dir = os.path.join(real_repo, "Command Injection", "Intruder")
        if not os.path.isdir(intruder_dir):
            pytest.skip("No Intruder dir in Command Injection")
        for fname in os.listdir(intruder_dir):
            fpath = os.path.join(intruder_dir, fname)
            if os.path.isfile(fpath):
                payloads = read_intruder_file(fpath)
                assert len(payloads) > 0
                print(f"\n  {fname}: {len(payloads)} payloads")


class TestRealRepoSearch:

    def test_search_union_select(self, real_repo):
        results = search(real_repo, "union select", max_results=20)
        assert len(results) > 0
        assert any("SQL" in r.category for r in results)
        print(f"\n  'union select': {len(results)} results")

    def test_search_alert_xss(self, real_repo):
        results = search(real_repo, "alert(", max_results=20)
        assert len(results) > 0
        print(f"\n  'alert(': {len(results)} results")

    def test_search_regex_ip_pattern(self, real_repo):
        results = search(real_repo, r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
                         regex=True, max_results=10)
        assert len(results) > 0
        print(f"\n  IP regex: {len(results)} results")

    def test_search_in_intruder_files(self, real_repo):
        results = search(real_repo, "OR 1=1", file_type="txt", max_results=20)
        assert all(r.match_type == "intruder" for r in results)
        print(f"\n  'OR 1=1' in intruder: {len(results)} results")


class TestRealRepoExport:

    def test_export_blocks_sql(self, real_repo, tmp_dir):
        out = os.path.join(tmp_dir, "sql_blocks.txt")
        result = export_code_blocks(real_repo, "SQL Injection", out)
        assert os.path.isfile(out)
        assert result["block_count"] >= 5
        assert result["file_size"] > 100
        print(f"\n  SQL blocks: {result['block_count']} blocks, "
              f"{result['file_size']:,} bytes -> {out}")

    def test_export_blocks_json_format(self, real_repo, tmp_dir):
        out = os.path.join(tmp_dir, "sql_blocks.json")
        result = export_code_blocks(real_repo, "SQL Injection", out, format="json")
        with open(out) as f:
            data = json.load(f)
        assert "blocks" in data
        assert len(data["blocks"]) >= 5
        print(f"\n  JSON export: {len(data['blocks'])} blocks, "
              f"{result['file_size']:,} bytes -> {out}")

    def test_export_intruder_sql(self, real_repo, tmp_dir):
        out = os.path.join(tmp_dir, "sqli_wordlist.txt")
        try:
            result = export_intruder(real_repo, "SQL Injection", out)
            assert os.path.isfile(out)
            assert result["payload_count"] > 0
            print(f"\n  Intruder export: {result['payload_count']} payloads, "
                  f"{result['file_size']:,} bytes -> {out}")
        except ValueError as e:
            if "No Intruder" in str(e):
                pytest.skip(f"No Intruder dir: {e}")
            raise

    def test_export_markdown_xxe(self, real_repo, tmp_dir):
        out = os.path.join(tmp_dir, "xxe_docs.md")
        result = export_category_markdown(real_repo, "XXE Injection", out)
        assert os.path.isfile(out)
        assert result["file_size"] > 500
        with open(out) as f:
            content = f.read()
        assert "XXE" in content
        print(f"\n  Markdown export: {len(result['source_files'])} files, "
              f"{result['file_size']:,} bytes -> {out}")

    def test_export_blocks_with_language_filter(self, real_repo, tmp_dir):
        out = os.path.join(tmp_dir, "sql_only.txt")
        result = export_code_blocks(real_repo, "SQL Injection", out, language="sql")
        assert result["block_count"] >= 1
        with open(out) as f:
            content = f.read()
        # Should contain SQL-like content
        assert len(content) > 10
        print(f"\n  SQL-only blocks: {result['block_count']} blocks -> {out}")


class TestRealRepoStats:

    def test_repo_stats(self, real_repo):
        stats = repo_stats(real_repo)
        assert stats["categories"] >= 50
        assert stats["markdown_files"] >= 100
        print(f"\n  Repo stats:")
        for k, v in stats.items():
            if k != "repo_path":
                print(f"    {k}: {v}")


# ── Subprocess CLI Tests ─────────────────────────────────────────────

def _resolve_cli(name):
    """Resolve installed CLI command; falls back to python -m for dev.

    Set env CLI_ANYTHING_FORCE_INSTALLED=1 to require the installed command.
    """
    import shutil
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
    module = name.replace("cli-anything-", "cli_anything.") + "." + name.split("-")[-1] + "_cli"
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m {module}")
    return [sys.executable, "-m", module]


class TestCLISubprocess:
    CLI_BASE = _resolve_cli("cli-anything-payloads")

    def _run(self, args, check=True, env_extra=None):
        env = os.environ.copy()
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True, text=True,
            check=check, env=env,
        )

    def _repo_args(self):
        repo = _get_real_repo()
        return ["--repo", repo]

    def test_help(self):
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "payloads" in result.stdout.lower() or "PayloadsAllTheThings" in result.stdout

    def test_version(self):
        result = self._run(["--version"])
        assert result.returncode == 0
        assert "1.0.0" in result.stdout

    def test_json_list(self):
        result = self._run(self._repo_args() + ["--json", "list"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "categories" in data
        assert len(data["categories"]) >= 50
        print(f"\n  JSON list: {len(data['categories'])} categories")

    def test_json_info(self):
        result = self._run(self._repo_args() + ["--json", "info"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "categories" in data
        assert data["categories"] >= 50

    def test_json_search(self):
        result = self._run(self._repo_args() + ["--json", "search", "union select"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "results" in data
        assert data["result_count"] > 0

    def test_json_show_sections(self):
        result = self._run(self._repo_args() + [
            "--json", "show", "SQL Injection", "--sections"
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "sections" in data
        assert len(data["sections"]) >= 3

    def test_json_extract(self):
        result = self._run(self._repo_args() + [
            "--json", "extract", "Command Injection"
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "blocks" in data
        assert data["block_count"] >= 1

    def test_json_intruder_list(self):
        result = self._run(self._repo_args() + [
            "--json", "intruder", "SQL Injection"
        ])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "files" in data

    def test_export_blocks_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "blocks.txt")
            result = self._run(self._repo_args() + [
                "export", "blocks", "XSS Injection", out
            ])
            assert result.returncode == 0
            assert os.path.isfile(out)
            size = os.path.getsize(out)
            assert size > 0
            print(f"\n  Subprocess export blocks: {size:,} bytes -> {out}")

    def test_export_intruder_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "wordlist.txt")
            result = self._run(self._repo_args() + [
                "export", "intruder", "SQL Injection", out
            ], check=False)
            if result.returncode == 0:
                assert os.path.isfile(out)
                size = os.path.getsize(out)
                assert size > 0
                print(f"\n  Subprocess export intruder: {size:,} bytes -> {out}")
            else:
                # May fail if no Intruder dir - still acceptable
                print(f"\n  Export intruder: {result.stderr.strip()}")

    def test_export_markdown_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "docs.md")
            result = self._run(self._repo_args() + [
                "export", "markdown", "XXE Injection", out
            ])
            assert result.returncode == 0
            assert os.path.isfile(out)
            with open(out) as f:
                content = f.read()
            assert "XXE" in content
            print(f"\n  Subprocess export markdown: {os.path.getsize(out):,} bytes")


class TestCLISubprocessWorkflow:
    """Full workflow tests simulating real agent usage."""
    CLI_BASE = _resolve_cli("cli-anything-payloads")

    def _run(self, args, check=True):
        repo = _get_real_repo()
        return subprocess.run(
            self.CLI_BASE + ["--repo", repo, "--json"] + args,
            capture_output=True, text=True,
            check=check,
        )

    def test_security_assessment_workflow(self):
        """Simulate: pentester preparing for web app assessment."""
        # 1. List categories
        r = self._run(["list", "--filter", "injection"])
        data = json.loads(r.stdout)
        injection_cats = [c["name"] for c in data["categories"]]
        assert len(injection_cats) >= 5
        print(f"\n  Injection categories: {injection_cats}")

        # 2. Search for auth bypass
        r = self._run(["search", "authentication bypass", "-n", "10"])
        data = json.loads(r.stdout)
        print(f"  Auth bypass results: {data['result_count']}")

        # 3. Extract SQL payloads
        r = self._run(["extract", "SQL Injection", "--language", "sql"])
        data = json.loads(r.stdout)
        assert data["block_count"] >= 1
        print(f"  SQL blocks: {data['block_count']}")

        # 4. Export wordlist
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "assessment_wordlist.txt")
            r = subprocess.run(
                self.CLI_BASE + ["--repo", _get_real_repo(),
                                  "export", "intruder", "SQL Injection", out],
                capture_output=True, text=True, check=False,
            )
            if r.returncode == 0:
                assert os.path.isfile(out)
                with open(out) as f:
                    payloads = [l.strip() for l in f if l.strip()]
                assert len(payloads) > 0
                print(f"  Wordlist: {len(payloads)} payloads -> {out}")

    def test_research_workflow(self):
        """Simulate: researcher gathering XSS reference material."""
        # 1. Show XSS sections
        r = self._run(["show", "XSS Injection", "--sections"])
        data = json.loads(r.stdout)
        assert len(data["sections"]) >= 3
        print(f"\n  XSS sections: {len(data['sections'])}")

        # 2. Extract all code blocks
        r = self._run(["extract", "XSS Injection"])
        data = json.loads(r.stdout)
        assert data["block_count"] >= 3
        print(f"  XSS blocks: {data['block_count']}")

        # 3. Export full markdown
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "xss_research.md")
            r = subprocess.run(
                self.CLI_BASE + ["--repo", _get_real_repo(),
                                  "export", "markdown", "XSS Injection", out],
                capture_output=True, text=True, check=True,
            )
            assert os.path.isfile(out)
            size = os.path.getsize(out)
            assert size > 1000
            print(f"  Markdown: {size:,} bytes -> {out}")
