# cli-anything-payloads

CLI harness for **PayloadsAllTheThings** — search, extract, and export security payloads from the command line.

## Requirements

- Python >= 3.10
- PayloadsAllTheThings repository (hard dependency):
  ```bash
  git clone https://github.com/swisskyrepo/PayloadsAllTheThings.git
  ```

## Installation

```bash
cd agent-harness
pip install -e .
```

Verify:
```bash
which cli-anything-payloads
cli-anything-payloads --help
```

## Usage

### Set repository path

```bash
export PAYLOADS_REPO=/path/to/PayloadsAllTheThings
# or use --repo flag
cli-anything-payloads --repo /path/to/PayloadsAllTheThings list
```

### List categories

```bash
cli-anything-payloads list
cli-anything-payloads list --filter "injection"
```

### Search payloads

```bash
cli-anything-payloads search "union select"
cli-anything-payloads search "bypass" --category "SQL Injection"
cli-anything-payloads search "\\bOR\\b.*1=1" --regex
```

### Show category info

```bash
cli-anything-payloads show "SQL Injection"
cli-anything-payloads show "SQL Injection" --sections
cli-anything-payloads info "XSS Injection"
cli-anything-payloads info  # whole repo stats
```

### Extract code blocks

```bash
cli-anything-payloads extract "SQL Injection" --language sql
cli-anything-payloads extract "Command Injection" --section "bypass"
```

### Browse intruder wordlists

```bash
cli-anything-payloads intruder "SQL Injection"
cli-anything-payloads intruder "SQL Injection" --file "Auth_Bypass.txt"
```

### Export to files

```bash
cli-anything-payloads export blocks "XSS Injection" xss_payloads.txt
cli-anything-payloads export blocks "SQL Injection" sqli.json --format json --language sql
cli-anything-payloads export intruder "Command Injection" wordlist.txt --deduplicate
cli-anything-payloads export markdown "SSRF" ssrf_docs.md
```

### JSON output (for agents)

```bash
cli-anything-payloads --json list
cli-anything-payloads --json search "reflected xss"
cli-anything-payloads --json extract "XXE Injection"
```

### Interactive REPL

```bash
cli-anything-payloads  # enters REPL mode
```

REPL commands: `list`, `show`, `search`, `extract`, `intruder`, `info`, `cd`, `fav`, `help`, `quit`

## Running Tests

```bash
cd agent-harness
pip install -e .
CLI_ANYTHING_FORCE_INSTALLED=1 python3 -m pytest cli_anything/payloads/tests/ -v -s
```
