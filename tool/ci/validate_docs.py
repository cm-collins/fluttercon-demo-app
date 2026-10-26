#!/usr/bin/env python3
"""Validate local Markdown links and extract Mermaid blocks for parser checks."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
IGNORED_DIRECTORIES = {
    ".dart_tool",
    ".git",
    ".idea",
    ".vscode",
    "build",
    "node_modules",
}
LINK_PATTERN = re.compile(r"!?\[[^\]]*]\(([^)\n]+)\)")
MERMAID_PATTERN = re.compile(
    r"^```mermaid[ \t]*\n(?P<body>.*?)^```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
URI_SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in REPOSITORY_ROOT.rglob("*.md")
        if not any(part in IGNORED_DIRECTORIES for part in path.parts)
    )


def link_destination(raw_destination: str) -> str:
    destination = raw_destination.strip()
    if destination.startswith("<") and ">" in destination:
        return destination[1 : destination.index(">")]
    return destination.split(maxsplit=1)[0]


def validate_local_links(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for markdown_file in files:
        text = markdown_file.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(text):
            destination = unquote(link_destination(match.group(1)))
            if (
                not destination
                or destination.startswith("#")
                or destination.startswith("//")
                or URI_SCHEME_PATTERN.match(destination)
            ):
                continue

            path_part = urlsplit(destination).path
            if not path_part:
                continue

            target = (
                REPOSITORY_ROOT / path_part.lstrip("/")
                if path_part.startswith("/")
                else markdown_file.parent / path_part
            )
            if not target.resolve().exists():
                relative_file = markdown_file.relative_to(REPOSITORY_ROOT)
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{relative_file}:{line}: missing local target {destination}")
    return errors


def extract_mermaid(files: list[Path], output_directory: Path) -> int:
    output_directory.mkdir(parents=True, exist_ok=True)
    count = 0
    for markdown_file in files:
        text = markdown_file.read_text(encoding="utf-8")
        for diagram_index, match in enumerate(MERMAID_PATTERN.finditer(text), start=1):
            count += 1
            relative = markdown_file.relative_to(REPOSITORY_ROOT)
            safe_name = "-".join(relative.with_suffix("").parts)
            output_file = output_directory / f"{safe_name}-{diagram_index:02d}.mmd"
            output_file.write_text(match.group("body").strip() + "\n", encoding="utf-8")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mermaid-dir",
        type=Path,
        help="Extract Mermaid blocks into this directory for validation by mmdc.",
    )
    arguments = parser.parse_args()

    files = markdown_files()
    errors = validate_local_links(files)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Validated local links in {len(files)} Markdown files.")
    if arguments.mermaid_dir:
        count = extract_mermaid(files, arguments.mermaid_dir)
        print(f"Extracted {count} Mermaid diagrams.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
