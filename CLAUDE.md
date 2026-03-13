# cli-anything-payloads — Agent Instructions

## Tool Overview

This repo contains `cli-anything-payloads`, a CLI harness for the PayloadsAllTheThings security payload repository. It provides structured search, extraction, and export of security payloads across 64 vulnerability categories, 142 markdown files, 67 Burp Intruder wordlists, and 133 exploit sample files.

## How to Use the CLI

Always activate the venv and pass the repo path:

```bash
source agent-harness/.venv/bin/activate && \
cli-anything-payloads --repo ./PayloadsAllTheThings --json <command>
```

Always use `--json` so output is machine-parseable. Never omit it unless the user specifically asks for human-readable output.

## Available Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `list` | Browse vulnerability categories | `--json list --filter "injection"` |
| `search <query>` | Full-text/regex search across all content | `--json search "union select" -c "SQL Injection"` |
| `show <category>` | Display category docs or section TOC | `--json show "XSS" --sections` |
| `info [category]` | Repo stats or category detail | `--json info "SQL Injection"` |
| `extract <category>` | Pull code blocks (filterable by language/section) | `--json extract "SQL Injection" -l sql` |
| `intruder <category>` | Browse/dump Burp Intruder wordlists | `--json intruder "SQL Injection" -f "Auth_Bypass.txt"` |
| `export blocks <cat> <out>` | Export code blocks to a file | `export blocks "XSS" payloads.txt --format json` |
| `export intruder <cat> <out>` | Export wordlists to a file | `export intruder "SQL Injection" wordlist.txt -d` |
| `export markdown <cat> <out>` | Export full markdown to a file | `export markdown "SSRF" ssrf.md` |

## Category Names Are Fuzzy-Matched

You don't need exact directory names. These all work:

- `"sql"` resolves to `SQL Injection`
- `"xss"` resolves to `XSS Injection`
- `"proto"` resolves to `Prototype Pollution`
- `"ssrf"` resolves to `Server Side Request Forgery`
- `"ssti"` resolves to `Server Side Template Injection`

If a name is ambiguous (e.g., `"injection"` matches 17 categories), the CLI returns an error listing all matches. Narrow the query or use the full name.

## Recommended Workflow

1. **Discover**: `--json list` or `--json info` to see what's available
2. **Search**: `--json search "<query>"` to find payloads across categories
3. **Drill down**: `--json show "<category>" --sections` to see structure, then `--json extract` to pull specific blocks
4. **Export**: `export blocks/intruder/markdown` to save to files when the user needs a deliverable
5. **Synthesize**: Combine extracted data with your own knowledge to produce tailored payload lists, assessment docs, or exploit scripts

## Important Notes

- The PayloadsAllTheThings repo lives at `./PayloadsAllTheThings/` relative to the repo root. Always use `--repo ./PayloadsAllTheThings`.
- If the venv doesn't exist yet, create it: `cd agent-harness && python3 -m venv .venv && source .venv/bin/activate && pip install -e .`
- The `--json` flag must go BEFORE the subcommand: `cli-anything-payloads --json search`, not `cli-anything-payloads search --json`.
- Export commands write real files. Use `--overwrite` if the output file already exists.
- Search supports `--regex` for pattern matching and `--category` to scope results.
- Intruder wordlists are plain-text files (one payload per line) designed for Burp Suite but useful for any fuzzing tool.
