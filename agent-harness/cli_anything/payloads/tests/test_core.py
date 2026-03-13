"""Unit tests for cli-anything-payloads core modules."""

import json
import os
import tempfile
import textwrap

import pytest

from cli_anything.payloads.core.repository import (
    find_repo, _is_repo, list_categories, resolve_category,
    category_info, repo_stats,
)
from cli_anything.payloads.core.parser import (
    parse_markdown, extract_code_blocks, extract_sections,
    read_intruder_file, count_code_blocks, CodeBlock,
)
from cli_anything.payloads.core.search import search, search_categories
from cli_anything.payloads.core.export import (
    export_code_blocks, export_intruder, export_category_markdown,
)
from cli_anything.payloads.core.session import Session


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def fake_repo(tmp_dir):
    """Create a minimal fake PayloadsAllTheThings repo structure."""
    repo = tmp_dir

    # Create marker categories
    for cat in ["SQL Injection", "XSS Injection", "Command Injection"]:
        cat_dir = os.path.join(repo, cat)
        os.makedirs(cat_dir)
        # README.md with code blocks
        readme = os.path.join(cat_dir, "README.md")
        with open(readme, "w") as f:
            f.write(textwrap.dedent(f"""\
                # {cat}
                > A description of {cat}

                ## Summary
                - [Tools](#tools)
                - [Methodology](#methodology)

                ## Tools
                - tool1
                - tool2

                ## Methodology

                Basic example:

                ```sql
                SELECT * FROM users WHERE id=1 OR 1=1
                ```

                Another technique:

                ```bash
                curl http://target/vuln?id=1' OR '1'='1
                ```

                ## Advanced

                ```python
                import requests
                r = requests.get("http://target/vuln", params={{"id": "1 OR 1=1"}})
                ```

                ## Labs
                - Lab 1
                - Lab 2

                ## References
                - https://example.com
            """))

    # Add intruder files to SQL Injection
    intruder_dir = os.path.join(repo, "SQL Injection", "Intruder")
    os.makedirs(intruder_dir)
    with open(os.path.join(intruder_dir, "Auth_Bypass.txt"), "w") as f:
        f.write("' OR 1=1--\n' OR '1'='1'\nadmin'--\n\" OR 1=1--\n")
    with open(os.path.join(intruder_dir, "SQLi_Generic.txt"), "w") as f:
        f.write("1 OR 1=1\n1' OR '1'='1\nUNION SELECT NULL\n")

    # Add a sub-topic .md file to SQL Injection
    with open(os.path.join(repo, "SQL Injection", "MySQL Injection.md"), "w") as f:
        f.write(textwrap.dedent("""\
            # MySQL Injection

            ## Default Databases
            ```sql
            SELECT schema_name FROM information_schema.schemata
            ```

            ## Union Based
            ```sql
            UNION SELECT 1,2,3--
            ```
        """))

    # Add Files dir to XSS
    files_dir = os.path.join(repo, "XSS Injection", "Files")
    os.makedirs(files_dir)
    with open(os.path.join(files_dir, "xss_payload.html"), "w") as f:
        f.write("<script>alert(1)</script>\n")

    # Add hidden and template dirs that should be skipped
    os.makedirs(os.path.join(repo, ".git"))
    os.makedirs(os.path.join(repo, "_template_vuln"))

    return repo


# ── repository.py tests ──────────────────────────────────────────────

class TestRepository:

    def test_is_repo_valid(self, fake_repo):
        assert _is_repo(fake_repo) is True

    def test_is_repo_invalid_empty(self, tmp_dir):
        assert _is_repo(tmp_dir) is False

    def test_is_repo_nonexistent(self):
        assert _is_repo("/nonexistent/path") is False

    def test_find_repo_valid(self, fake_repo):
        result = find_repo(fake_repo)
        assert result == os.path.abspath(fake_repo)

    def test_find_repo_invalid(self, tmp_dir):
        with pytest.raises(RuntimeError, match="Not a valid"):
            find_repo(tmp_dir)

    def test_find_repo_none(self):
        with pytest.raises(RuntimeError, match="No repository path"):
            find_repo(None)

    def test_list_categories(self, fake_repo):
        cats = list_categories(fake_repo)
        names = [c["name"] for c in cats]
        assert "SQL Injection" in names
        assert "XSS Injection" in names
        assert "Command Injection" in names
        # Skipped dirs
        assert ".git" not in names
        assert "_template_vuln" not in names

    def test_list_categories_properties(self, fake_repo):
        cats = list_categories(fake_repo)
        sql_cat = next(c for c in cats if c["name"] == "SQL Injection")
        assert sql_cat["has_readme"] is True
        assert sql_cat["has_intruder"] is True
        assert len(sql_cat["intruder_files"]) == 2

    def test_resolve_category_exact(self, fake_repo):
        assert resolve_category(fake_repo, "SQL Injection") == "SQL Injection"

    def test_resolve_category_case_insensitive(self, fake_repo):
        assert resolve_category(fake_repo, "sql injection") == "SQL Injection"

    def test_resolve_category_substring(self, fake_repo):
        assert resolve_category(fake_repo, "XSS") == "XSS Injection"

    def test_resolve_category_not_found(self, fake_repo):
        with pytest.raises(ValueError, match="Category not found"):
            resolve_category(fake_repo, "Nonexistent Category")

    def test_resolve_category_ambiguous(self, fake_repo):
        # "Injection" matches all three
        with pytest.raises(ValueError, match="Ambiguous"):
            resolve_category(fake_repo, "Injection")

    def test_category_info(self, fake_repo):
        info = category_info(fake_repo, "SQL Injection")
        assert info["name"] == "SQL Injection"
        assert len(info["md_files"]) == 2  # README.md + MySQL Injection.md
        assert len(info["intruder_files"]) == 2

    def test_repo_stats(self, fake_repo):
        stats = repo_stats(fake_repo)
        assert stats["categories"] == 3
        assert stats["markdown_files"] >= 4  # READMEs + MySQL
        assert stats["intruder_wordlists"] == 2


# ── parser.py tests ──────────────────────────────────────────────────

class TestParser:

    def test_parse_markdown_sections(self, fake_repo):
        fpath = os.path.join(fake_repo, "SQL Injection", "README.md")
        sections = parse_markdown(fpath)
        titles = [s.title for s in sections]
        assert "SQL Injection" in titles

    def test_extract_code_blocks_all(self, fake_repo):
        fpath = os.path.join(fake_repo, "SQL Injection", "README.md")
        blocks = extract_code_blocks(fpath)
        assert len(blocks) == 3  # sql, bash, python

    def test_extract_code_blocks_filter_language(self, fake_repo):
        fpath = os.path.join(fake_repo, "SQL Injection", "README.md")
        blocks = extract_code_blocks(fpath, language="sql")
        assert len(blocks) == 1
        assert "SELECT" in blocks[0].content

    def test_extract_code_blocks_filter_section(self, fake_repo):
        fpath = os.path.join(fake_repo, "SQL Injection", "README.md")
        blocks = extract_code_blocks(fpath, section_filter="Advanced")
        assert len(blocks) == 1
        assert blocks[0].language == "python"

    def test_extract_sections_flat(self, fake_repo):
        fpath = os.path.join(fake_repo, "SQL Injection", "README.md")
        secs = extract_sections(fpath)
        titles = [s["title"] for s in secs]
        assert "Summary" in titles
        assert "Methodology" in titles
        assert "Advanced" in titles

    def test_code_block_to_dict(self, fake_repo):
        fpath = os.path.join(fake_repo, "SQL Injection", "README.md")
        blocks = extract_code_blocks(fpath)
        d = blocks[0].to_dict()
        assert "language" in d
        assert "content" in d
        assert "section" in d

    def test_read_intruder_file(self, fake_repo):
        fpath = os.path.join(fake_repo, "SQL Injection", "Intruder", "Auth_Bypass.txt")
        payloads = read_intruder_file(fpath)
        assert len(payloads) == 4
        assert "' OR 1=1--" in payloads

    def test_read_intruder_file_skips_empty(self, tmp_dir):
        fpath = os.path.join(tmp_dir, "test.txt")
        with open(fpath, "w") as f:
            f.write("payload1\n\n\npayload2\n")
        payloads = read_intruder_file(fpath)
        assert len(payloads) == 2

    def test_count_code_blocks(self, fake_repo):
        fpath = os.path.join(fake_repo, "SQL Injection", "README.md")
        counts = count_code_blocks(fpath)
        assert counts.get("sql", 0) == 1
        assert counts.get("bash", 0) == 1
        assert counts.get("python", 0) == 1


# ── search.py tests ──────────────────────────────────────────────────

class TestSearch:

    def test_search_basic(self, fake_repo):
        results = search(fake_repo, "OR 1=1")
        assert len(results) > 0
        assert any("SQL Injection" in r.category for r in results)

    def test_search_case_insensitive(self, fake_repo):
        results = search(fake_repo, "select")
        assert len(results) > 0

    def test_search_case_sensitive(self, fake_repo):
        results_upper = search(fake_repo, "SELECT", case_sensitive=True)
        results_lower = search(fake_repo, "select", case_sensitive=True)
        # SELECT is in the code, "select" lowercase may not be
        assert len(results_upper) > 0

    def test_search_regex(self, fake_repo):
        results = search(fake_repo, r"OR\s+\d+=\d+", regex=True)
        assert len(results) > 0

    def test_search_category_filter(self, fake_repo):
        results = search(fake_repo, "SELECT", category="SQL Injection")
        assert all(r.category == "SQL Injection" for r in results)

    def test_search_file_type_filter(self, fake_repo):
        results = search(fake_repo, "OR 1=1", file_type="txt")
        assert all(r.match_type == "intruder" for r in results)

    def test_search_max_results(self, fake_repo):
        results = search(fake_repo, "OR", max_results=2)
        assert len(results) <= 2

    def test_search_context_lines(self, fake_repo):
        results = search(fake_repo, "SELECT", context_lines=3)
        if results:
            # Context should be populated
            r = results[0]
            assert isinstance(r.context_before, list)
            assert isinstance(r.context_after, list)

    def test_search_categories(self, fake_repo):
        matches = search_categories(fake_repo, "SQL")
        assert "SQL Injection" in matches

    def test_search_no_results(self, fake_repo):
        results = search(fake_repo, "zzz_nonexistent_string_zzz")
        assert len(results) == 0

    def test_search_invalid_regex(self, fake_repo):
        with pytest.raises(ValueError, match="Invalid regex"):
            search(fake_repo, "[invalid", regex=True)


# ── export.py tests ──────────────────────────────────────────────────

class TestExport:

    def test_export_code_blocks_raw(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "blocks.txt")
        result = export_code_blocks(fake_repo, "SQL Injection", out)
        assert os.path.isfile(out)
        assert result["block_count"] > 0
        assert result["file_size"] > 0
        with open(out) as f:
            content = f.read()
        assert "SELECT" in content

    def test_export_code_blocks_json(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "blocks.json")
        result = export_code_blocks(fake_repo, "SQL Injection", out, format="json")
        with open(out) as f:
            data = json.load(f)
        assert "blocks" in data
        assert len(data["blocks"]) > 0

    def test_export_code_blocks_numbered(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "blocks_num.txt")
        result = export_code_blocks(fake_repo, "SQL Injection", out, format="numbered")
        with open(out) as f:
            content = f.read()
        assert "Block 1" in content

    def test_export_code_blocks_language_filter(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "sql_only.txt")
        result = export_code_blocks(fake_repo, "SQL Injection", out, language="sql")
        assert result["block_count"] >= 1
        assert "sql" in result["languages"]

    def test_export_code_blocks_no_overwrite(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "exists.txt")
        with open(out, "w") as f:
            f.write("existing")
        with pytest.raises(FileExistsError):
            export_code_blocks(fake_repo, "SQL Injection", out)

    def test_export_code_blocks_overwrite(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "exists.txt")
        with open(out, "w") as f:
            f.write("existing")
        result = export_code_blocks(fake_repo, "SQL Injection", out, overwrite=True)
        assert result["block_count"] > 0

    def test_export_intruder(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "wordlist.txt")
        result = export_intruder(fake_repo, "SQL Injection", out)
        assert os.path.isfile(out)
        assert result["payload_count"] == 7  # 4 + 3 from both files
        with open(out) as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) == 7

    def test_export_intruder_specific_file(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "auth.txt")
        result = export_intruder(fake_repo, "SQL Injection", out,
                                  filename="Auth_Bypass.txt")
        assert result["payload_count"] == 4

    def test_export_intruder_deduplicate(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "dedup.txt")
        result = export_intruder(fake_repo, "SQL Injection", out, deduplicate=True)
        assert result["payload_count"] <= result["original_count"]

    def test_export_intruder_no_dir(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "nope.txt")
        with pytest.raises(ValueError, match="No Intruder"):
            export_intruder(fake_repo, "XSS Injection", out)

    def test_export_category_markdown(self, fake_repo, tmp_dir):
        out = os.path.join(tmp_dir, "sql.md")
        result = export_category_markdown(fake_repo, "SQL Injection", out)
        assert os.path.isfile(out)
        assert result["file_size"] > 0
        assert len(result["source_files"]) == 2
        with open(out) as f:
            content = f.read()
        assert "SQL Injection" in content
        assert "MySQL Injection" in content


# ── session.py tests ─────────────────────────────────────────────────

class TestSession:

    def test_session_create(self, tmp_dir):
        sf = os.path.join(tmp_dir, "session.json")
        session = Session(session_file=sf)
        assert session.current_category is None
        assert session.favorites == []

    def test_session_current_category(self, tmp_dir):
        sf = os.path.join(tmp_dir, "session.json")
        session = Session(session_file=sf)
        session.current_category = "SQL Injection"
        assert session.current_category == "SQL Injection"
        # Reload
        session2 = Session(session_file=sf)
        assert session2.current_category == "SQL Injection"

    def test_session_favorites(self, tmp_dir):
        sf = os.path.join(tmp_dir, "session.json")
        session = Session(session_file=sf)
        session.add_favorite("XSS Injection")
        session.add_favorite("SQL Injection")
        assert len(session.favorites) == 2
        session.add_favorite("XSS Injection")  # duplicate
        assert len(session.favorites) == 2
        session.remove_favorite("XSS Injection")
        assert len(session.favorites) == 1
        assert "SQL Injection" in session.favorites

    def test_session_search_history(self, tmp_dir):
        sf = os.path.join(tmp_dir, "session.json")
        session = Session(session_file=sf)
        session.add_search("union select")
        session.add_search("xss payload")
        assert len(session.search_history) == 2
        # Dedup replaces old entry
        session.add_search("union select")
        assert len(session.search_history) == 2

    def test_session_clear(self, tmp_dir):
        sf = os.path.join(tmp_dir, "session.json")
        session = Session(session_file=sf)
        session.current_category = "SQL Injection"
        session.add_favorite("XSS")
        session.clear()
        assert session.current_category is None
        assert session.favorites == []

    def test_session_to_dict(self, tmp_dir):
        sf = os.path.join(tmp_dir, "session.json")
        session = Session(session_file=sf)
        d = session.to_dict()
        assert "current_category" in d
        assert "favorites" in d
        assert "search_history" in d
