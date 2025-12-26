#!/usr/bin/env python3
"""
Convert RST files to Markdown and Jupyter Notebooks.

This script converts all .rst files in the 'rst' directory to:
- Markdown files in the 'markdown' directory
- Jupyter notebooks in the 'notebook' directory

Requirements:
    pip install nbformat

Usage:
    python convert_rst.py
"""

import os
import re
import sys
from pathlib import Path

try:
    import nbformat
    from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
except ImportError:
    print("Error: nbformat is not installed. Install it with: pip install nbformat")
    sys.exit(1)


def expand_tabs(text: str, tab_size: int = 4) -> str:
    """Expand tabs to spaces, preserving alignment."""
    return text.expandtabs(tab_size)


def is_code_continuation(line: str) -> bool:
    """Check if a line looks like it continues a code block (starts with whitespace)."""
    return bool(line) and (line[0] == " " or line[0] == "\t")


def rst_to_markdown(rst_content: str) -> str:
    """Convert RST content to Markdown."""
    # Expand tabs to spaces for consistent indentation handling
    rst_content = expand_tabs(rst_content)
    lines = rst_content.split("\n")
    result = []
    i = 0
    skip_until_dedent = False
    skip_indent_level = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Calculate current indentation
        indent = len(line) - len(line.lstrip()) if line.strip() else 0

        # Skip testsetup, testcleanup, testoutput blocks entirely
        if re.match(r"\.\.\s+(testsetup|testcleanup|testoutput)::", stripped):
            i += 1
            # Skip all indented content and blank lines within
            base_indent = indent
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                next_indent = (
                    len(next_line) - len(next_line.lstrip()) if next_stripped else 0
                )

                if (
                    next_stripped
                    and next_indent <= base_indent
                    and not next_line.startswith(" ")
                ):
                    break
                i += 1
            continue

        # Skip highlight directive
        if re.match(r"\.\.\s+highlight::", stripped):
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith(" ")):
                if lines[i].strip() and not lines[i].strip().startswith(":"):
                    break
                i += 1
            continue

        # Skip only:: html blocks
        if re.match(r"\.\.\s+only::\s+html", stripped):
            i += 1
            base_indent = indent
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                next_indent = (
                    len(next_line) - len(next_line.lstrip()) if next_stripped else 0
                )
                if (
                    next_stripped
                    and next_indent <= base_indent
                    and not next_line.startswith(" ")
                ):
                    break
                i += 1
            continue

        # Skip index directives
        if re.match(r"\.\.\s+index::", stripped):
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith(" ")):
                i += 1
            continue

        # Skip target definitions like .. _name:
        if re.match(r"\.\.\s+_[\w-]+:\s*$", stripped):
            i += 1
            continue

        # Handle title underlines/overlines (===, ---, ***, etc.)
        if i + 1 < len(lines) and stripped and lines[i + 1].strip():
            underline = lines[i + 1].strip()
            if (
                len(set(underline)) == 1
                and underline[0] in "=-~*+^\"'"
                and len(underline) >= 3
            ):
                title = stripped
                underline_char = underline[0]

                # Map underline characters to heading levels
                level_map = {"*": 1, "=": 2, "-": 3, "~": 4, "+": 5, "^": 6}
                level = level_map.get(underline_char, 2)

                # Check for overline (previous line same as underline)
                if result and result[-1].strip():
                    prev = result[-1].strip()
                    if len(set(prev)) == 1 and prev[0] == underline_char:
                        result.pop()  # Remove overline
                        level = 1  # Overlined titles are typically top-level

                result.append("")
                result.append("#" * level + " " + title)
                result.append("")
                i += 2  # Skip the underline
                continue

        # Handle testcode blocks
        if re.match(r"\.\.\s+testcode::", stripped):
            i += 1
            # Skip empty lines
            while i < len(lines) and not lines[i].strip():
                i += 1

            result.append("")
            result.append("```python")

            # Find the base indentation of the code
            if i < len(lines) and lines[i].strip():
                code_base_indent = len(lines[i]) - len(lines[i].lstrip())
            else:
                code_base_indent = 4

            # Collect indented code
            while i < len(lines):
                code_line = lines[i]
                code_stripped = code_line.strip()
                code_indent = (
                    len(code_line) - len(code_line.lstrip()) if code_stripped else 0
                )

                # Stop if we hit a non-indented, non-empty line
                if code_stripped and code_indent < code_base_indent:
                    break

                if code_stripped:
                    # Remove base indentation
                    result.append(
                        code_line[code_base_indent:]
                        if len(code_line) > code_base_indent
                        else code_line.lstrip()
                    )
                else:
                    result.append("")
                i += 1

            # Remove trailing empty lines
            while result and not result[-1].strip() and result[-1] != "```python":
                result.pop()

            result.append("```")
            result.append("")
            continue

        # Handle code-block directive
        code_block_match = re.match(r"\.\.\s+code-block::\s*(\w+)?", stripped)
        if code_block_match:
            lang = code_block_match.group(1) or "python"
            i += 1

            # Skip empty lines and options
            while i < len(lines) and (
                not lines[i].strip() or lines[i].strip().startswith(":")
            ):
                i += 1

            result.append("")
            result.append(f"```{lang}")

            # Find base indentation
            if i < len(lines) and lines[i].strip():
                code_base_indent = len(lines[i]) - len(lines[i].lstrip())
            else:
                code_base_indent = 4

            # Collect indented code
            while i < len(lines):
                code_line = lines[i]
                code_stripped = code_line.strip()
                code_indent = (
                    len(code_line) - len(code_line.lstrip()) if code_stripped else 0
                )

                if code_stripped and code_indent < code_base_indent:
                    break

                if code_stripped:
                    result.append(
                        code_line[code_base_indent:]
                        if len(code_line) > code_base_indent
                        else code_line.lstrip()
                    )
                else:
                    result.append("")
                i += 1

            while result and not result[-1].strip():
                result.pop()

            result.append("```")
            result.append("")
            continue

        # Handle :: code blocks (literal blocks)
        if stripped.endswith("::") and not stripped.startswith(".."):
            prefix = stripped[:-2].rstrip()
            if prefix:
                result.append(prefix + ":")

            i += 1
            # Skip empty lines
            while i < len(lines) and not lines[i].strip():
                i += 1

            if i < len(lines) and (
                lines[i].startswith("  ") or lines[i].startswith("\t")
            ):
                # Find base indentation
                code_base_indent = len(lines[i]) - len(lines[i].lstrip())

                # Collect code first to determine language
                code_lines = []
                temp_i = i
                while temp_i < len(lines):
                    code_line = lines[temp_i]
                    code_stripped = code_line.strip()
                    code_indent = (
                        len(code_line) - len(code_line.lstrip()) if code_stripped else 0
                    )

                    if code_stripped and code_indent < code_base_indent:
                        break

                    if code_stripped:
                        code_lines.append(
                            code_line[code_base_indent:]
                            if len(code_line) > code_base_indent
                            else code_line.lstrip()
                        )
                    else:
                        code_lines.append("")
                    temp_i += 1

                # Remove trailing empty lines
                while code_lines and not code_lines[-1].strip():
                    code_lines.pop()

                # Detect language based on content
                code_content = "\n".join(code_lines)
                lang = "python"  # default

                # Check for INI/config file patterns
                if (
                    re.search(r"^\[.*\]", code_content, re.MULTILINE)
                    or re.search(r"^;\s*", code_content, re.MULTILINE)
                    or re.search(r"^\w+\s*=\s*\w", code_content, re.MULTILINE)
                ):
                    # Has INI-style sections, comments, or key=value
                    if not re.search(
                        r"^\s*(def|class|import|from|if|for|while|try|with)\s",
                        code_content,
                        re.MULTILINE,
                    ):
                        lang = "ini"

                result.append("")
                result.append(f"```{lang}")
                for code_line in code_lines:
                    result.append(code_line)
                result.append("```")
                result.append("")

                i = temp_i
            continue

        # Handle figure directive
        fig_match = re.match(r"\.\.\s+figure::\s*(.+)", stripped)
        if fig_match:
            img_path = fig_match.group(1).strip()
            i += 1

            caption = ""
            # Skip options and find caption
            while i < len(lines) and (
                lines[i].startswith("   ") or not lines[i].strip()
            ):
                option_line = lines[i].strip()
                if option_line and not option_line.startswith(":"):
                    caption = option_line
                i += 1

            result.append("")
            result.append(f"![{caption}]({img_path})")
            if caption:
                result.append(f"*{caption}*")
            result.append("")
            continue

        # Handle hint, note, warning directives
        directive_match = re.match(
            r"\.\.\s+(hint|note|warning|tip|important)::\s*(.*)", stripped
        )
        if directive_match:
            directive_type = directive_match.group(1)
            inline_content = directive_match.group(2).strip()
            i += 1

            # Collect all content from the directive first to check for code blocks
            base_indent = indent + 3  # Standard RST indent
            directive_content = []
            code_blocks = []
            text_lines = []

            while i < len(lines):
                content_line = lines[i]
                content_stripped = content_line.strip()
                content_indent = (
                    len(content_line) - len(content_line.lstrip())
                    if content_stripped
                    else 0
                )

                # Stop at dedent (non-indented, non-empty line)
                if (
                    content_stripped
                    and content_indent < base_indent
                    and not content_line.startswith(" ")
                ):
                    break

                # Check for nested code blocks (testcode)
                if re.match(r"\.\.\s+testcode::", content_stripped):
                    i += 1
                    while i < len(lines) and not lines[i].strip():
                        i += 1

                    code_lines = []
                    if i < len(lines) and lines[i].strip():
                        code_base_indent = len(lines[i]) - len(lines[i].lstrip())
                    else:
                        code_base_indent = 4

                    while i < len(lines):
                        code_line = lines[i]
                        code_stripped = code_line.strip()
                        code_indent = (
                            len(code_line) - len(code_line.lstrip())
                            if code_stripped
                            else 0
                        )

                        if code_stripped and code_indent < code_base_indent:
                            break

                        if code_stripped:
                            code_lines.append(
                                code_line[code_base_indent:]
                                if len(code_line) > code_base_indent
                                else code_line.lstrip()
                            )
                        else:
                            code_lines.append("")
                        i += 1

                    # Remove trailing empty lines from code
                    while code_lines and not code_lines[-1].strip():
                        code_lines.pop()

                    if code_lines:
                        code_blocks.append("\n".join(code_lines))
                    continue

                if content_stripped:
                    text = (
                        content_line[base_indent:]
                        if len(content_line) > base_indent
                        else content_stripped
                    )
                    text_lines.append(text)
                else:
                    text_lines.append("")
                i += 1

            # Remove trailing empty lines from text
            while text_lines and not text_lines[-1].strip():
                text_lines.pop()

            # Output: First the hint text as a note
            result.append("")
            hint_text = inline_content if inline_content else ""
            if text_lines:
                hint_text = (hint_text + " " if hint_text else "") + " ".join(
                    line for line in text_lines if line.strip()
                )

            result.append(
                f"**{directive_type.capitalize()}:** {hint_text}"
                if hint_text
                else f"**{directive_type.capitalize()}**"
            )
            result.append("")

            # Output code blocks as regular (executable) code blocks
            for code in code_blocks:
                result.append("```python")
                result.append(code)
                result.append("```")
                result.append("")

            continue

        # Skip other unknown directives
        if re.match(r"\.\.\s+\w+::", stripped) and not stripped.startswith(".. code"):
            i += 1
            # Skip indented content
            base_indent = indent + 1
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                next_indent = (
                    len(next_line) - len(next_line.lstrip()) if next_stripped else 0
                )
                if next_stripped and next_indent <= indent:
                    break
                i += 1
            continue

        # Convert inline RST to Markdown
        converted_line = line

        # Convert :role:`text` patterns
        converted_line = re.sub(r":file:`([^`]+)`", r"`\1`", converted_line)
        converted_line = re.sub(r":menuselection:`([^`]+)`", r"**\1**", converted_line)
        converted_line = re.sub(r":command:`([^`]+)`", r"`\1`", converted_line)
        converted_line = re.sub(r":data:`([^`]+)`", r"`\1`", converted_line)
        converted_line = re.sub(r":const:`([^`]+)`", r"`\1`", converted_line)
        converted_line = re.sub(r":kbd:`([^`]+)`", r"<kbd>\1</kbd>", converted_line)
        converted_line = re.sub(r":guilabel:`([^`]+)`", r"**\1**", converted_line)
        converted_line = re.sub(r":envvar:`([^`]+)`", r"`\1`", converted_line)

        # Handle :class:`ClassName <module.ClassName>` role
        converted_line = re.sub(r":class:`([^<`]+)\s*<[^>]+>`", r"`\1`", converted_line)
        converted_line = re.sub(r":class:`([^`]+)`", r"`\1`", converted_line)

        # Handle :meth:`method() <module.Class.method>` role
        converted_line = re.sub(r":meth:`([^<`]+)\s*<[^>]+>`", r"`\1`", converted_line)
        converted_line = re.sub(r":meth:`([^`]+)`", r"`\1`", converted_line)

        # Handle :func:`function` role
        converted_line = re.sub(r":func:`([^<`]+)\s*<[^>]+>`", r"`\1`", converted_line)
        converted_line = re.sub(r":func:`([^`]+)`", r"`\1`", converted_line)

        # Handle :attr:`attribute` role
        converted_line = re.sub(r":attr:`([^<`]+)\s*<[^>]+>`", r"`\1`", converted_line)
        converted_line = re.sub(r":attr:`([^`]+)`", r"`\1`", converted_line)

        # Handle :mod:`module` role
        converted_line = re.sub(r":mod:`([^`]+)`", r"`\1`", converted_line)

        # Handle :ref:`label` role - keep as italic for cross-references
        converted_line = re.sub(r":ref:`([^`]+)`", r"*\1*", converted_line)

        # Handle :doc:`document` role
        converted_line = re.sub(r":doc:`([^`]+)`", r"*\1*", converted_line)

        # Handle :api:`text <>` role
        converted_line = re.sub(r":api:`([^<`]*)\s*<[^>]*>`", r"\1", converted_line)

        # Handle :pyqgis:`text <>` role
        converted_line = re.sub(r":pyqgis:`([^<`]*)\s*<[^>]*>`", r"\1", converted_line)

        # Handle :source:`text <path>` role
        converted_line = re.sub(
            r":source:`([^<`]+)\s*<([^>]+)>`", r"[\1](\2)", converted_line
        )

        # Convert ``code`` to `code`
        converted_line = re.sub(r"``([^`]+)``", r"`\1`", converted_line)

        # Convert `link text <url>`_ to [link text](url)
        converted_line = re.sub(r"`([^<]+)\s*<([^>]+)>`_+", r"[\1](\2)", converted_line)

        # Convert standalone `text`_ references (external links defined elsewhere)
        # Leave them as-is for now since we'd need to look up the target

        result.append(converted_line)
        i += 1

    # Clean up multiple empty lines
    cleaned = []
    prev_empty = False
    for line in result:
        is_empty = not line.strip()
        if is_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = is_empty

    # Remove leading/trailing empty lines
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    return "\n".join(cleaned)


def markdown_to_notebook(
    markdown_content: str, title: str = ""
) -> nbformat.NotebookNode:
    """Convert Markdown content to a Jupyter notebook."""
    nb = new_notebook()
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {"name": "python", "version": "3.9.0"}

    lines = markdown_content.split("\n")
    cells = []
    current_lines = []
    in_code_block = False
    code_lang = ""
    code_fence_pattern = ""
    in_quote = False
    quote_code_block = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Handle code blocks inside quotes
        if line.startswith("> ```"):
            if not in_quote:
                in_quote = True
            if quote_code_block:
                # End of quoted code block
                current_lines.append(line)
                quote_code_block = False
            else:
                # Start of quoted code block
                current_lines.append(line)
                quote_code_block = True
            i += 1
            continue

        if quote_code_block:
            current_lines.append(line)
            i += 1
            continue

        # Check for code block start (not in quote)
        code_start = re.match(r"^(```+)\s*(\w*)$", line)
        if code_start and not in_code_block:
            # Save current markdown content
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    cells.append(("markdown", content))
                current_lines = []

            in_code_block = True
            code_fence_pattern = code_start.group(1)
            code_lang = code_start.group(2) or ""
            i += 1
            continue

        # Check for code block end
        if in_code_block and line.strip() == code_fence_pattern:
            in_code_block = False
            content = "\n".join(current_lines).strip()
            if content:
                # Only treat as executable code if explicitly Python or no language specified
                # and content looks like Python code
                is_python = code_lang in ("python", "py", "")
                if is_python and code_lang == "":
                    # Check if it looks like Python code (simple heuristics)
                    # If it has common non-Python patterns, treat as markdown
                    non_python_patterns = [
                        r"^[A-Z_]+\s*=",  # ENV_VAR = value
                        r"^\s*#.*bin/",  # shebang-like
                        r"^\s*<",  # XML/HTML
                        r"^\s*\[.*\]",  # INI sections
                        r"^export\s+",  # bash export
                        r"^set\s+",  # batch set
                        r"^call\s+",  # batch call
                        r"^@echo",  # batch echo
                        r"^path\s+",  # batch path
                        r"^Start\s+",  # batch Start
                        r"^\s*initialize the",  # plain text description
                        r"^\s*create the",  # plain text description
                        r"^\s*the main",  # plain text description
                        r"^\s*for each",  # plain text description
                    ]
                    for pattern in non_python_patterns:
                        if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                            is_python = False
                            break

                if is_python and code_lang in ("python", "py", ""):
                    cells.append(("code", content))
                else:
                    # Non-Python code blocks stay as markdown
                    lang_tag = code_lang if code_lang else "text"
                    cells.append(("markdown", f"```{lang_tag}\n{content}\n```"))
            current_lines = []
            code_fence_pattern = ""
            code_lang = ""
            i += 1
            continue

        current_lines.append(line)
        i += 1

    # Handle remaining content
    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            if in_code_block and code_lang in ("python", "py"):
                cells.append(("code", content))
            else:
                cells.append(("markdown", content))

    # Combine consecutive markdown cells
    combined_cells = []
    current_md = []

    for cell_type, content in cells:
        if cell_type == "markdown":
            current_md.append(content)
        else:
            if current_md:
                combined_cells.append(("markdown", "\n\n".join(current_md)))
                current_md = []
            combined_cells.append((cell_type, content))

    if current_md:
        combined_cells.append(("markdown", "\n\n".join(current_md)))

    # Create actual cells
    for cell_type, content in combined_cells:
        if cell_type == "code":
            nb.cells.append(new_code_cell(content))
        else:
            nb.cells.append(new_markdown_cell(content))

    # Ensure at least one cell
    if not nb.cells:
        nb.cells.append(new_markdown_cell(f"# {title}" if title else "# Untitled"))

    return nb


def convert_file(
    rst_path: Path, markdown_dir: Path, notebook_dir: Path, base_rst_dir: Path
):
    """Convert a single RST file to Markdown and Jupyter notebook."""
    # Calculate relative path from rst directory
    rel_path = rst_path.relative_to(base_rst_dir)

    # Create output paths
    md_path = markdown_dir / rel_path.with_suffix(".md")
    nb_path = notebook_dir / rel_path.with_suffix(".ipynb")

    # Create output directories if they don't exist
    md_path.parent.mkdir(parents=True, exist_ok=True)
    nb_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Converting: {rel_path}")

    # Read RST content
    with open(rst_path, "r", encoding="utf-8") as f:
        rst_content = f.read()

    try:
        # Convert to Markdown
        markdown_content = rst_to_markdown(rst_content)

        # Write Markdown file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"  → Markdown: {md_path.relative_to(markdown_dir.parent)}")

        # Convert to Jupyter notebook
        title = rst_path.stem.replace("_", " ").title()
        notebook = markdown_to_notebook(markdown_content, title)

        # Write notebook file
        with open(nb_path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)
        print(f"  → Notebook: {nb_path.relative_to(notebook_dir.parent)}")

        return True
    except Exception as e:
        print(f"  Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function to convert all RST files."""
    # Get the script directory
    script_dir = Path(__file__).parent.resolve()

    # Define directories
    rst_dir = script_dir / "rst"
    markdown_dir = script_dir / "markdown"
    notebook_dir = script_dir / "notebook"

    # Check if rst directory exists
    if not rst_dir.exists():
        print(f"Error: RST directory not found: {rst_dir}")
        sys.exit(1)

    # Create output directories
    markdown_dir.mkdir(exist_ok=True)
    notebook_dir.mkdir(exist_ok=True)

    # Find all RST files
    rst_files = list(rst_dir.rglob("*.rst"))

    if not rst_files:
        print(f"No RST files found in {rst_dir}")
        sys.exit(1)

    print(f"Found {len(rst_files)} RST files to convert")
    print("=" * 60)

    # Convert each file
    success_count = 0
    fail_count = 0

    for rst_file in sorted(rst_files):
        if convert_file(rst_file, markdown_dir, notebook_dir, rst_dir):
            success_count += 1
        else:
            fail_count += 1

    print("=" * 60)
    print(f"\nConversion complete!")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"\nMarkdown files: {markdown_dir}")
    print(f"Notebook files: {notebook_dir}")


if __name__ == "__main__":
    main()
