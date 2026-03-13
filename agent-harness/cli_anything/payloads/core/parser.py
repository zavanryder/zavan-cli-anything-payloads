"""Markdown parser for extracting payloads and structure from .md files."""

import os
import re
from dataclasses import dataclass, field


@dataclass
class CodeBlock:
    """A fenced code block extracted from markdown."""
    language: str
    content: str
    line_start: int
    line_end: int
    section: str  # The heading this block appears under
    file_path: str = ""

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "content": self.content,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "section": self.section,
            "file_path": self.file_path,
        }


@dataclass
class Section:
    """A markdown section (heading + content)."""
    title: str
    level: int
    line_start: int
    content: str
    code_blocks: list[CodeBlock] = field(default_factory=list)
    subsections: list["Section"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "level": self.level,
            "line_start": self.line_start,
            "code_blocks": [cb.to_dict() for cb in self.code_blocks],
            "subsections": [s.to_dict() for s in self.subsections],
        }


def parse_markdown(file_path: str) -> list[Section]:
    """Parse a markdown file into sections with extracted code blocks.

    Args:
        file_path: Path to the markdown file.

    Returns:
        List of top-level Section objects.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    sections = []
    current_section = None
    in_code_block = False
    code_lang = ""
    code_start = 0
    code_lines = []

    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()

        # Handle fenced code blocks
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = stripped[3:].strip().split()[0] if len(stripped) > 3 else ""
                code_start = i
                code_lines = []
            else:
                in_code_block = False
                block = CodeBlock(
                    language=code_lang,
                    content="\n".join(code_lines),
                    line_start=code_start,
                    line_end=i,
                    section=current_section.title if current_section else "",
                    file_path=file_path,
                )
                if current_section:
                    current_section.code_blocks.append(block)
                elif sections:
                    sections[-1].code_blocks.append(block)
            continue

        if in_code_block:
            code_lines.append(line.rstrip("\n"))
            continue

        # Handle headings
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            section = Section(
                title=title,
                level=level,
                line_start=i,
                content="",
            )
            if level == 1 or not sections:
                sections.append(section)
                current_section = section
            elif current_section and level > current_section.level:
                current_section.subsections.append(section)
                current_section = section
            else:
                # Find parent at appropriate level
                sections.append(section)
                current_section = section
            continue

        # Accumulate content
        if current_section is not None:
            current_section.content += line

    return sections


def extract_code_blocks(file_path: str, language: str | None = None,
                        section_filter: str | None = None) -> list[CodeBlock]:
    """Extract all code blocks from a markdown file.

    Args:
        file_path: Path to the markdown file.
        language: Filter by language tag (e.g., "sql", "bash"). None = all.
        section_filter: Filter by section title substring. None = all.

    Returns:
        List of CodeBlock objects.
    """
    sections = parse_markdown(file_path)
    blocks = []

    def _collect(section_list: list[Section]):
        for sec in section_list:
            for block in sec.code_blocks:
                if language and block.language.lower() != language.lower():
                    continue
                if section_filter and section_filter.lower() not in sec.title.lower():
                    continue
                blocks.append(block)
            _collect(sec.subsections)

    _collect(sections)
    return blocks


def extract_sections(file_path: str) -> list[dict]:
    """Extract section headings as a flat list (table of contents).

    Returns:
        List of dicts with title, level, line_start, code_block_count.
    """
    sections = parse_markdown(file_path)
    flat = []

    def _flatten(section_list: list[Section]):
        for sec in section_list:
            flat.append({
                "title": sec.title,
                "level": sec.level,
                "line_start": sec.line_start,
                "code_block_count": len(sec.code_blocks),
            })
            _flatten(sec.subsections)

    _flatten(sections)
    return flat


def read_intruder_file(file_path: str) -> list[str]:
    """Read an intruder wordlist file (one payload per line).

    Args:
        file_path: Path to the .txt wordlist file.

    Returns:
        List of payload strings (empty lines excluded).
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return [line.rstrip("\n\r") for line in f if line.strip()]


def count_code_blocks(file_path: str) -> dict[str, int]:
    """Count code blocks by language in a markdown file.

    Returns:
        Dict mapping language -> count. Empty string key for untagged blocks.
    """
    blocks = extract_code_blocks(file_path)
    counts: dict[str, int] = {}
    for b in blocks:
        lang = b.language or "(none)"
        counts[lang] = counts.get(lang, 0) + 1
    return counts
