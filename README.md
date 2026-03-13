# cli-anything-payloads

A stateful CLI harness for [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) — search, extract, and export security payloads without leaving the terminal.

Built with the cli-anything methodology: every command supports `--json` for machine consumption, making it usable by both humans and AI agents — particularly **Claude Code**, which can call the CLI via Bash to research, assemble, and export payloads as part of security assessment workflows.

```
╭──────────────────────────────────────────────────────╮
│ ◆  cli-anything · Payloads                           │
│    v1.0.0                                            │
│                                                      │
│    Type help for commands, quit to exit               │
╰──────────────────────────────────────────────────────╯
```

## What It Does

PayloadsAllTheThings is a massive reference repo: 64 vulnerability categories, 142 markdown files, 67 Burp Intruder wordlists, and 133 exploit sample files. This CLI gives you structured access to all of it:

- **Search** across every payload, wordlist, and document with text or regex
- **Extract** code blocks filtered by language (`sql`, `bash`, `js`, etc.) or section
- **Browse** Burp Intruder wordlists by category
- **Export** payloads to files in raw, JSON, or numbered format
- **REPL** mode with session state, favorites, and command history

## Requirements

- Python >= 3.10
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) repository (hard dependency)

## Installation

PayloadsAllTheThings must be cloned **into the root of this repository** so it lives at `PayloadOfAllThings/PayloadsAllTheThings/`. The CLI expects this layout:

```
PayloadOfAllThings/          # <-- this repo
├── PayloadsAllTheThings/    # <-- clone goes HERE
├── agent-harness/
└── README.md
```

```bash
# 1. Clone PayloadsAllTheThings into the repo root (if not already present)
cd PayloadOfAllThings
git clone https://github.com/swisskyrepo/PayloadsAllTheThings.git

# 2. Create a venv and install the CLI
cd agent-harness
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 3. Verify
which cli-anything-payloads
cli-anything-payloads --version
```

## Quick Start

```bash
# Set the repo path (points to the PayloadsAllTheThings/ directory inside this repo)
export PAYLOADS_REPO=/path/to/PayloadOfAllThings/PayloadsAllTheThings

# Or pass it every time with --repo
cli-anything-payloads --repo ./PayloadsAllTheThings list
```

## Commands

### `list` — Browse vulnerability categories

```bash
cli-anything-payloads list
cli-anything-payloads list --filter "injection"
```

```
  Categories (64):

    Account Takeover
    API Key Leaks
    Command Injection  (intruder:2)
    CORS Misconfiguration
    ...
    SQL Injection  (intruder:15, files)
    XSS Injection  (files)
    XXE Injection
```

### `search` — Full-text and regex search

```bash
# Text search across all markdown and wordlists
cli-anything-payloads search "union select"

# Scoped to a category
cli-anything-payloads search "bypass" --category "SQL Injection"

# Regex search
cli-anything-payloads search "\bOR\b.*1=1" --regex

# Only in intruder wordlists
cli-anything-payloads search "admin" --type txt

# Case-sensitive with extra context
cli-anything-payloads search "SELECT" --case-sensitive --context 3
```

### `show` — Read category documentation

```bash
# Full README content
cli-anything-payloads show "SQL Injection"

# Table of contents only
cli-anything-payloads show "SQL Injection" --sections

# Specific sub-file
cli-anything-payloads show "SQL Injection" --file "MySQL Injection.md"
```

### `info` — Repository and category stats

```bash
# Whole repo overview
cli-anything-payloads info

# Single category detail
cli-anything-payloads info "XSS Injection"
```

```
  PayloadsAllTheThings Repository
  Path: /home/user/PayloadsAllTheThings
  Categories: 64
  Markdown files: 142
  Intruder wordlists: 67
  Sample files: 133
  Categories with Intruder: 8
```

### `extract` — Pull code blocks from documentation

```bash
# All code blocks from a category
cli-anything-payloads extract "SQL Injection"

# Filter by language
cli-anything-payloads extract "SQL Injection" --language sql

# Filter by section heading
cli-anything-payloads extract "Command Injection" --section "bypass"

# Single block by index
cli-anything-payloads extract "XSS Injection" --index 3
```

### `intruder` — Browse Burp Suite wordlists

```bash
# List available wordlists for a category
cli-anything-payloads intruder "SQL Injection"

# Dump a specific wordlist
cli-anything-payloads intruder "SQL Injection" --file "Auth_Bypass.txt"

# Preview first 20 lines
cli-anything-payloads intruder "Command Injection" --file "command_exec.txt" --head 20
```

### `export` — Save payloads to files

```bash
# Code blocks → raw text file
cli-anything-payloads export blocks "XSS Injection" xss_payloads.txt

# Code blocks → structured JSON
cli-anything-payloads export blocks "SQL Injection" sqli.json --format json --language sql

# Code blocks → numbered with metadata
cli-anything-payloads export blocks "XXE Injection" xxe.txt --format numbered

# Intruder wordlists → merged file
cli-anything-payloads export intruder "SQL Injection" sqli_wordlist.txt

# Intruder → deduplicated
cli-anything-payloads export intruder "SQL Injection" sqli_dedup.txt --deduplicate

# Full category markdown → single file
cli-anything-payloads export markdown "Prototype Pollution" pp_reference.md
```

### `session` — Manage state

```bash
cli-anything-payloads session status
cli-anything-payloads session favorite "SQL Injection"
cli-anything-payloads session favorite "XSS Injection" --remove
cli-anything-payloads session clear
```

## JSON Mode

Every command supports `--json` for agent/script consumption:

```bash
cli-anything-payloads --json list
cli-anything-payloads --json search "reflected xss"
cli-anything-payloads --json extract "XXE Injection"
cli-anything-payloads --json info
```

Example JSON output:

```json
{
  "query": "union select",
  "result_count": 20,
  "results": [
    {
      "file_path": "SQL Injection/README.md",
      "category": "SQL Injection",
      "line_number": 87,
      "line_content": "UNION SELECT 1,2,3--",
      "match_type": "markdown"
    }
  ]
}
```

## Interactive REPL

Run with no subcommand to enter the REPL:

```bash
cli-anything-payloads --repo ./PayloadsAllTheThings
```

REPL commands:

| Command | Description |
|---------|-------------|
| `list [filter]` | List categories |
| `show <category>` | Show section headings |
| `search <query>` | Search payloads |
| `extract <category>` | Extract code blocks |
| `intruder <category>` | Browse wordlists |
| `info [category]` | Repo or category stats |
| `cd <category>` | Set current category (used as default) |
| `fav <category>` | Toggle favorite |
| `favorites` | List favorites |
| `help` | Show all commands |
| `quit` | Exit |

The REPL maintains session state across invocations — current category, favorites, search history, and command history are persisted to `~/.cli-anything-payloads/`.

## Using with Claude Code

The `--json` flag makes every command machine-parseable, which means Claude Code can call the CLI via Bash and reason over structured payload data. This is the primary design goal — giving an AI agent direct, queryable access to the entire PayloadsAllTheThings corpus.

### Setup

Make sure the venv is activated in your shell before starting Claude Code, or activate it inline:

```bash
# Option A: activate before launching Claude
cd PayloadOfAllThings/agent-harness
source .venv/bin/activate
export PAYLOADS_REPO=/path/to/PayloadOfAllThings/PayloadsAllTheThings
claude

# Option B: Claude can activate inline in each Bash call
source agent-harness/.venv/bin/activate && cli-anything-payloads --repo ./PayloadsAllTheThings --json list
```

### CLAUDE.md

This repo includes a [`CLAUDE.md`](./CLAUDE.md) file in the project root. Claude Code automatically reads `CLAUDE.md` at the start of every conversation when working in this directory, so it already knows how to use the tool without being told.

The file contains:
- **Activation command** — the exact `source ... && cli-anything-payloads` invocation pattern so Claude always activates the venv and passes `--repo`
- **Command reference table** — every subcommand with its purpose and a concrete example, so Claude can pick the right one without running `--help` first
- **Fuzzy matching guide** — explains that short names like `"sql"` and `"proto"` work, so Claude doesn't waste time typing full directory names
- **Recommended workflow** — the Discover → Search → Drill down → Export → Synthesize pattern that produces the best results
- **Gotchas** — `--json` must come before the subcommand, `--overwrite` is needed for existing files, etc.

This means you can just open Claude Code in this directory and ask payload-related questions directly — no setup instructions needed in your prompt.

### Example Prompts and What Claude Does

**"Find all SQL injection authentication bypass payloads"**

Claude runs:
```bash
source agent-harness/.venv/bin/activate && \
cli-anything-payloads --repo ./PayloadsAllTheThings --json search "authentication bypass" \
  --category "SQL Injection" -n 30
```
Then parses the JSON results, reads the relevant file sections, and summarizes the techniques.

---

**"Extract all XSS payloads that use JavaScript and export them to a file"**

Claude runs:
```bash
source agent-harness/.venv/bin/activate && \
cli-anything-payloads --repo ./PayloadsAllTheThings \
  export blocks "XSS Injection" xss_js_payloads.txt --language javascript --overwrite
```

---

**"What intruder wordlists are available for command injection? Dump the exec one."**

Claude runs two commands:
```bash
# 1. List available wordlists
cli-anything-payloads --repo ./PayloadsAllTheThings --json intruder "Command Injection"

# 2. Dump the specific file
cli-anything-payloads --repo ./PayloadsAllTheThings --json intruder "Command Injection" \
  --file "command_exec.txt"
```

---

**"Build me a prototype pollution payload list for an ExpressJS app using PUG templates"**

Claude chains multiple queries:
```bash
# 1. Get all prototype pollution code blocks
cli-anything-payloads --repo ./PayloadsAllTheThings --json extract "Prototype Pollution"

# 2. Search for Express-specific detection techniques
cli-anything-payloads --repo ./PayloadsAllTheThings --json search "express" \
  --category "Prototype Pollution"

# 3. Get PUG template injection payloads from SSTI
cli-anything-payloads --repo ./PayloadsAllTheThings --json extract \
  "Server Side Template Injection" --section "Pug"

# 4. Search for RCE gadgets
cli-anything-payloads --repo ./PayloadsAllTheThings --json search "RCE" \
  --category "Prototype Pollution"
```
Then Claude synthesizes the results into a combined payload document with detection, exploitation, and bypass sections.

---

**"Give me a quick overview of what's in this repo"**

Claude runs:
```bash
cli-anything-payloads --repo ./PayloadsAllTheThings --json info
```

Returns:
```json
{
  "categories": 64,
  "markdown_files": 142,
  "intruder_wordlists": 67,
  "sample_files": 133,
  "categories_with_intruder": 8
}
```

---

**"What categories cover injection attacks?"**

```bash
cli-anything-payloads --repo ./PayloadsAllTheThings --json list --filter "injection"
```

Returns 17 categories: CRLF Injection, CSS Injection, Command Injection, GraphQL Injection, LDAP Injection, LaTeX Injection, NoSQL Injection, Prompt Injection, SQL Injection, SSTI, XPATH, XSLT, XSS, XXE, etc.

### Why `--json` Matters

Without `--json`, the CLI outputs human-formatted text with ANSI colors and tables. With `--json`, Claude gets structured data it can parse with `json.loads()` and reason over programmatically:

| Without `--json` | With `--json` |
|---|---|
| Colored terminal output | Clean JSON objects |
| Tables with box-drawing chars | Arrays of dicts |
| Good for humans in REPL | Good for Claude via Bash tool |

Claude should **always** use `--json` when calling this tool. The human-readable mode is for interactive REPL sessions.

### Workflow Pattern

The typical Claude Code workflow with this tool is:

1. **Discover** — `--json list` or `--json info` to understand what's available
2. **Search** — `--json search` to find relevant payloads across categories
3. **Extract** — `--json extract` to pull structured code blocks with language/section metadata
4. **Export** — `export blocks/intruder/markdown` to save payloads to files
5. **Synthesize** — Claude combines extracted data with its own knowledge to produce tailored payload lists, write test scripts, or build assessment documentation

## Project Structure

```
PayloadOfAllThings/
├── README.md                          # This file
├── CLAUDE.md                          # Agent instructions (auto-loaded by Claude Code)
├── PayloadsAllTheThings/              # The upstream repo (hard dependency)
└── agent-harness/
    ├── PAYLOADS.md                    # Software-specific SOP
    ├── setup.py                       # PyPI package config
    └── cli_anything/                  # Namespace package (no __init__.py)
        └── payloads/
            ├── __init__.py
            ├── __main__.py            # python3 -m cli_anything.payloads
            ├── payloads_cli.py        # Main CLI (Click groups + REPL)
            ├── README.md              # Package-level docs
            ├── core/
            │   ├── repository.py      # Repo discovery, category listing, fuzzy match
            │   ├── parser.py          # Markdown → sections + code blocks
            │   ├── search.py          # Full-text + regex search engine
            │   ├── export.py          # Export blocks/intruder/markdown to files
            │   └── session.py         # Persistent session state (JSON)
            ├── utils/
            │   ├── repo_backend.py    # Repo validation + clone helper
            │   └── repl_skin.py       # Branded REPL interface
            └── tests/
                ├── TEST.md            # Test plan + results (80/80 passed)
                ├── test_core.py       # 52 unit tests (synthetic data)
                └── test_full_e2e.py   # 28 E2E + subprocess tests (real repo)
```

## Running Tests

```bash
cd agent-harness
source .venv/bin/activate
pip install pytest

# Run all tests against the installed CLI
# PAYLOADS_REPO must point to the PayloadsAllTheThings/ directory inside this repo
export PAYLOADS_REPO=/path/to/PayloadOfAllThings/PayloadsAllTheThings
CLI_ANYTHING_FORCE_INSTALLED=1 python3 -m pytest cli_anything/payloads/tests/ -v -s
```

```
80 passed in 0.98s
```

| Suite | Tests | Description |
|-------|-------|-------------|
| `test_core.py` | 52 | Unit tests — repository, parser, search, export, session |
| `test_full_e2e.py` | 28 | E2E against real repo + subprocess tests via installed CLI |

## Fuzzy Category Matching

Category names are fuzzy-matched, so you don't need to type exact directory names:

```bash
cli-anything-payloads show "sql"        # → SQL Injection
cli-anything-payloads show "xss"        # → XSS Injection
cli-anything-payloads show "xxe"        # → XXE Injection
cli-anything-payloads show "ssrf"       # → Server Side Request Forgery
cli-anything-payloads show "ssti"       # → Server Side Template Injection
cli-anything-payloads show "proto"      # → Prototype Pollution
```

Case-insensitive, substring, and multi-word matching are all supported. Ambiguous matches return a helpful error listing the candidates.

## License

The CLI harness is provided as-is. PayloadsAllTheThings is maintained by [swisskyrepo](https://github.com/swisskyrepo) under its own license.
