# PayloadsAllTheThings — CLI Harness SOP

## Software Overview

**PayloadsAllTheThings** is a comprehensive security payload reference repository
containing 68+ vulnerability categories with markdown documentation, code-block
payloads, Burp Suite Intruder wordlists, and exploit sample files.

Unlike typical cli-anything targets (GUI applications), PayloadsAllTheThings is a
**knowledge base**. The "backend" is the repository filesystem itself. The CLI
provides structured search, extraction, and export of security payloads.

## Architecture

### Data Model

```
Repository Root
├── Category/                   # e.g., "SQL Injection", "XSS Injection"
│   ├── README.md               # Main documentation with payloads in code blocks
│   ├── *.md                    # Sub-topic files (e.g., "MySQL Injection.md")
│   ├── Intruder/               # Burp Suite wordlists (.txt, one payload per line)
│   ├── Files/                  # Exploit samples (.py, .php, .xml, .zip, etc.)
│   └── Images/                 # Diagrams and screenshots
```

### Content Types

1. **Markdown payloads** — Code blocks in README.md with language tags (sql, bash, js, etc.)
2. **Intruder wordlists** — Plain-text files, one payload per line
3. **Sample files** — Exploit scripts, configs, templates
4. **Documentation** — Methodology descriptions, tool references, lab links

### Backend

The repository itself is the backend dependency. The CLI must have a valid
PayloadsAllTheThings checkout to operate. It indexes the filesystem and parses
markdown to extract structured payload data.

## Command Groups

| Group     | Purpose                                          |
|-----------|--------------------------------------------------|
| `list`    | List categories, files, code blocks              |
| `show`    | Display category documentation or payload detail |
| `search`  | Full-text search across all content              |
| `extract` | Extract code blocks or intruder wordlists        |
| `export`  | Export payloads to files                         |
| `info`    | Repository statistics and metadata               |
| `session` | Manage session state (favorites, history)        |

## Required Dependency

- **PayloadsAllTheThings repository** — Must be cloned locally.
  ```bash
  git clone https://github.com/swisskyrepo/PayloadsAllTheThings.git
  ```
