# Test Plan — cli-anything-payloads

## Test Inventory

- `test_core.py`: ~30 unit tests planned
- `test_full_e2e.py`: ~20 E2E + subprocess tests planned

## Unit Test Plan (`test_core.py`)

### repository.py
- `find_repo()` — valid path, invalid path, parent-with-subdir detection
- `_is_repo()` — real repo vs empty dir vs non-existent
- `list_categories()` — returns correct count, skips hidden/template dirs
- `resolve_category()` — exact match, case-insensitive, substring, ambiguous, not found
- `category_info()` — correct file counts per type
- `repo_stats()` — overall statistics accuracy

### parser.py
- `parse_markdown()` — headings, nested sections, code blocks
- `extract_code_blocks()` — all blocks, language filter, section filter
- `extract_sections()` — flat TOC generation
- `read_intruder_file()` — line-per-payload, empty line exclusion
- `count_code_blocks()` — language distribution

### search.py
- `search()` — basic text, case-insensitive, regex, category filter, file_type filter
- `search()` — context lines, max_results limit
- `search_categories()` — name substring matching

### export.py
- `export_code_blocks()` — raw, json, numbered formats
- `export_intruder()` — single file, merge all, deduplication
- `export_category_markdown()` — single file aggregation

### session.py
- `Session` — create, load, save, current_category, favorites CRUD
- `Session.add_search()` — history tracking with dedup
- `Session.clear()` — full state reset

## E2E Test Plan (`test_full_e2e.py`)

### Real Repository Tests
- List categories from real repo — verify known categories exist
- Show "SQL Injection" sections — verify expected headings
- Extract code blocks from "XSS Injection" — verify blocks exist with content
- Search "union select" — verify matches in SQL Injection files
- Read intruder files from "Command Injection" — verify payloads loaded
- Export code blocks to file — verify file created with content
- Export intruder wordlists — verify file with payloads
- Export with deduplication — verify count reduced

### Subprocess Tests (TestCLISubprocess)
- `--help` — exits 0
- `--version` — shows version string
- `--json list` — valid JSON with categories array
- `--json search "select"` — valid JSON with results
- `--json info` — valid JSON with repo stats
- `--json extract "Command Injection"` — valid JSON with blocks
- `export blocks` — file created via subprocess
- `export intruder` — wordlist file created via subprocess

## Realistic Workflow Scenarios

### Scenario 1: Security Assessment Prep
**Simulates:** Pentester preparing payloads for a web app assessment
1. List all injection categories
2. Search for "authentication bypass"
3. Extract SQL injection payloads filtered by language
4. Export intruder wordlists for Burp Suite
5. **Verified:** Exported files contain valid, non-empty payloads

### Scenario 2: Research & Documentation
**Simulates:** Security researcher gathering reference material
1. Show XSS Injection sections (TOC)
2. Extract all code blocks
3. Export full markdown documentation
4. **Verified:** Exported markdown preserves structure and content

### Scenario 3: Agent-Driven Payload Selection
**Simulates:** AI agent selecting payloads via JSON API
1. JSON list → get all categories
2. JSON search → find relevant payloads
3. JSON extract → get structured code blocks
4. **Verified:** All JSON output is valid, parseable, and contains expected fields

---

## Test Results

**Date:** 2026-03-12
**Python:** 3.13.5 | **pytest:** 9.0.2 | **CLI_ANYTHING_FORCE_INSTALLED:** 1

```
[_resolve_cli] Using installed command: .venv/bin/cli-anything-payloads

cli_anything/payloads/tests/test_core.py::TestRepository::test_is_repo_valid PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_is_repo_invalid_empty PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_is_repo_nonexistent PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_find_repo_valid PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_find_repo_invalid PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_find_repo_none PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_list_categories PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_list_categories_properties PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_resolve_category_exact PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_resolve_category_case_insensitive PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_resolve_category_substring PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_resolve_category_not_found PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_resolve_category_ambiguous PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_category_info PASSED
cli_anything/payloads/tests/test_core.py::TestRepository::test_repo_stats PASSED
cli_anything/payloads/tests/test_core.py::TestParser::test_parse_markdown_sections PASSED
cli_anything/payloads/tests/test_core.py::TestParser::test_extract_code_blocks_all PASSED
cli_anything/payloads/tests/test_core.py::TestParser::test_extract_code_blocks_filter_language PASSED
cli_anything/payloads/tests/test_core.py::TestParser::test_extract_code_blocks_filter_section PASSED
cli_anything/payloads/tests/test_core.py::TestParser::test_extract_sections_flat PASSED
cli_anything/payloads/tests/test_core.py::TestParser::test_code_block_to_dict PASSED
cli_anything/payloads/tests/test_core.py::TestParser::test_read_intruder_file PASSED
cli_anything/payloads/tests/test_core.py::TestParser::test_read_intruder_file_skips_empty PASSED
cli_anything/payloads/tests/test_core.py::TestParser::test_count_code_blocks PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_basic PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_case_insensitive PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_case_sensitive PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_regex PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_category_filter PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_file_type_filter PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_max_results PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_context_lines PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_categories PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_no_results PASSED
cli_anything/payloads/tests/test_core.py::TestSearch::test_search_invalid_regex PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_code_blocks_raw PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_code_blocks_json PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_code_blocks_numbered PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_code_blocks_language_filter PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_code_blocks_no_overwrite PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_code_blocks_overwrite PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_intruder PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_intruder_specific_file PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_intruder_deduplicate PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_intruder_no_dir PASSED
cli_anything/payloads/tests/test_core.py::TestExport::test_export_category_markdown PASSED
cli_anything/payloads/tests/test_core.py::TestSession::test_session_create PASSED
cli_anything/payloads/tests/test_core.py::TestSession::test_session_current_category PASSED
cli_anything/payloads/tests/test_core.py::TestSession::test_session_favorites PASSED
cli_anything/payloads/tests/test_core.py::TestSession::test_session_search_history PASSED
cli_anything/payloads/tests/test_core.py::TestSession::test_session_clear PASSED
cli_anything/payloads/tests/test_core.py::TestSession::test_session_to_dict PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoListing::test_list_categories_has_known_entries PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoListing::test_category_info_sql_injection PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoParser::test_extract_sections_sql_injection PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoParser::test_extract_code_blocks_xss PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoParser::test_intruder_wordlists_command_injection PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoSearch::test_search_union_select PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoSearch::test_search_alert_xss PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoSearch::test_search_regex_ip_pattern PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoSearch::test_search_in_intruder_files PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoExport::test_export_blocks_sql PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoExport::test_export_blocks_json_format PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoExport::test_export_intruder_sql PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoExport::test_export_markdown_xxe PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoExport::test_export_blocks_with_language_filter PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestRealRepoStats::test_repo_stats PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_help PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_version PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_json_list PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_json_info PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_json_search PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_json_show_sections PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_json_extract PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_json_intruder_list PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_export_blocks_subprocess PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_export_intruder_subprocess PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocess::test_export_markdown_subprocess PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocessWorkflow::test_security_assessment_workflow PASSED
cli_anything/payloads/tests/test_full_e2e.py::TestCLISubprocessWorkflow::test_research_workflow PASSED

============================== 80 passed in 0.98s ==============================
```

### Summary

| Metric | Value |
|--------|-------|
| Total tests | 80 |
| Passed | 80 |
| Failed | 0 |
| Pass rate | 100% |
| Execution time | 0.98s |

### Test Breakdown

| Test File | Tests | Description |
|-----------|-------|-------------|
| `test_core.py` | 52 | Unit tests with synthetic data (repository, parser, search, export, session) |
| `test_full_e2e.py` | 28 | E2E tests against real repo + subprocess tests via installed CLI |

### Key Artifacts Produced

- SQL code blocks: 148 blocks, 25,726 bytes
- SQL JSON export: 148 blocks, 66,507 bytes
- SQL intruder wordlist: 1,465 payloads, 78,274 bytes
- XXE markdown: 28,683 bytes
- XSS research markdown: 74,660 bytes

### Coverage Notes

- All core modules fully tested (repository, parser, search, export, session)
- Real repo E2E covers listing, parsing, searching, exporting
- Subprocess tests confirm installed CLI works end-to-end with `_resolve_cli()`
- REPL mode not tested via automated tests (interactive mode requires TTY)
