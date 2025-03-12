# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0


import json
import re
import shutil
from pathlib import Path
from typing import Optional

from ..import_utils import optional_import_block, require_optional_import
from .utils import NavigationGroup, copy_files, get_git_tracked_and_untracked_files_in_directory

with optional_import_block():
    from jinja2 import Template


def filter_excluded_files(files: list[Path], exclusion_list: list[str], website_dir: Path) -> list[Path]:
    return [
        file
        for file in files
        if not any(Path(str(file.relative_to(website_dir))).as_posix().startswith(excl) for excl in exclusion_list)
    ]


def copy_file(file: Path, mkdocs_output_dir: Path) -> None:
    dest = mkdocs_output_dir / file.relative_to(file.parents[1])
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file, dest)


def transform_tab_component(content: str) -> str:
    """Transform React-style tab components to MkDocs tab components.

    Args:
        content: String containing React-style tab components.
            Expected format is:
            <Tabs>
                <Tab title="Title 1">
                    content 1
                </Tab>
                <Tab title="Title 2">
                    content 2
                </Tab>
            </Tabs>

    Returns:
        String with MkDocs tab components:
            === "Title 1"
                content 1

            === "Title 2"
                content 2
    """
    if "<Tabs>" not in content:
        return content

    # Find and replace each Tabs section
    pattern = re.compile(r"<Tabs>(.*?)</Tabs>", re.DOTALL)

    def replace_tabs(match: re.Match[str]) -> str:
        tabs_content = match.group(1)

        # Extract all Tab elements
        tab_pattern = re.compile(r'<Tab title="([^"]+)">(.*?)</Tab>', re.DOTALL)
        tabs = tab_pattern.findall(tabs_content)

        if not tabs:
            return ""

        result = []

        for i, (title, tab_content) in enumerate(tabs):
            # Add tab header
            result.append(f'=== "{title}"')

            # Process content by maintaining indentation structure
            lines = tab_content.strip().split("\n")

            # Find minimum common indentation for non-empty lines
            non_empty_lines = [line for line in lines if line.strip()]
            min_indent = min([len(line) - len(line.lstrip()) for line in non_empty_lines]) if non_empty_lines else 0

            # Remove common indentation and add 4-space indent
            processed_lines = []
            for line in lines:
                if line.strip():
                    # Remove the common indentation but preserve relative indentation
                    if len(line) >= min_indent:
                        processed_lines.append("    " + line[min_indent:])
                    else:
                        processed_lines.append("    " + line.lstrip())
                else:
                    processed_lines.append("")

            result.append("\n".join(processed_lines))

            # Add a blank line between tabs (but not after the last one)
            if i < len(tabs) - 1:
                result.append("")

        return "\n".join(result)

    # Replace each Tabs section
    result = pattern.sub(replace_tabs, content)

    return result


def transform_card_grp_component(content: str) -> str:
    # Replace CardGroup tags
    modified_content = re.sub(r"<CardGroup\s+cols=\{(\d+)\}>\s*", "", content)
    modified_content = re.sub(r"\s*</CardGroup>", "", modified_content)

    # Replace Card tags with title and href attributes
    pattern = r'<Card\s+title="([^"]*)"\s+href="([^"]*)">(.*?)</Card>'
    replacement = r'<a class="card" href="\2">\n<h2>\1</h2>\3</a>'
    modified_content = re.sub(pattern, replacement, modified_content, flags=re.DOTALL)

    # Replace simple Card tags
    modified_content = re.sub(r"<Card>", '<div class="card">', modified_content)
    modified_content = re.sub(r"</Card>", "</div>", modified_content)

    return modified_content


def fix_asset_path(content: str) -> str:
    # Replace static/img paths with ag2/assets/img
    modified_content = re.sub(r'src="/static/img/([^"]+)"', r'src="/assets/img/\1"', content)

    # Replace docs paths with ag2/docs
    modified_content = re.sub(r'href="/docs/([^"]+)"', r'href="/docs/\1"', modified_content)

    return modified_content


def transform_content_for_mkdocs(content: str) -> str:
    # Transform admonitions (Tip, Warning, Note)
    tag_mappings = {
        "Tip": "tip",
        "Warning": "warning",
        "Note": "note",
        "Danger": "danger",
    }
    for html_tag, mkdocs_type in tag_mappings.items():
        pattern = f"<{html_tag}>(.*?)</{html_tag}>"

        def replacement(match: re.Match[str]) -> str:
            inner_content = match.group(1).strip()

            lines = inner_content.split("\n")

            non_empty_lines = [line for line in lines if line.strip()]
            min_indent = min([len(line) - len(line.lstrip()) for line in non_empty_lines]) if non_empty_lines else 0

            # Process each line
            processed_lines = []
            for line in lines:
                if line.strip():
                    # Remove common indentation and add 4-space indent
                    if len(line) >= min_indent:
                        processed_lines.append("    " + line[min_indent:])
                    else:
                        processed_lines.append("    " + line.lstrip())
                else:
                    processed_lines.append("")

            # Format the admonition with properly indented content
            return f"!!! {mkdocs_type.lstrip()}\n" + "\n".join(processed_lines)

        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Clean up style tags with double curly braces
    style_pattern = r"style\s*=\s*{{\s*([^}]+)\s*}}"

    def style_replacement(match: re.Match[str]) -> str:
        style_content = match.group(1).strip()
        return f"style={{ {style_content} }}"

    content = re.sub(style_pattern, style_replacement, content)

    # Transform tab components
    content = transform_tab_component(content)

    # Transform CardGroup components
    content = transform_card_grp_component(content)

    # Fix assets path
    content = fix_asset_path(content)

    return content


def process_and_copy_files(input_dir: Path, output_dir: Path, files: list[Path]) -> None:
    for file in files:
        if file.suffix == ".mdx":
            content = file.read_text()
            processed_content = transform_content_for_mkdocs(content)
            dest = output_dir / file.relative_to(input_dir).with_suffix(".md")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(processed_content)
        else:
            copy_files(input_dir, output_dir, [file])
            # copy_file(file, output_dir)


def format_title(title: str, keywords: dict[str, str]) -> str:
    """Format a page title with proper capitalization for special keywords."""
    words = title.replace("-", " ").title().split()
    return " ".join(keywords.get(word, word) for word in words)


def format_page_entry(page_path: str, indent: str, keywords: dict[str, str]) -> str:
    """Format a single page entry as either a parenthesized path or a markdown link."""
    path = f"{page_path}.md"
    title = format_title(Path(page_path).name, keywords)
    return f"{indent}    - [{title}]({path})"


def format_navigation(nav: list[NavigationGroup], depth: int = 0, keywords: Optional[dict[str, str]] = None) -> str:
    """
    Recursively format navigation structure into markdown-style nested list.

    Args:
        nav: List of navigation items with groups and pages
        depth: Current indentation depth
        keywords: Dictionary of special case word capitalizations

    Returns:
        Formatted navigation as a string
    """
    if keywords is None:
        keywords = {
            "Ag2": "AG2",
            "Rag": "RAG",
            "Llm": "LLM",
        }

    indent = "    " * depth
    result = []

    for item in nav:
        # Add group header
        result.append(f"{indent}- {item['group']}")

        # Process each page
        for page in item["pages"]:
            if isinstance(page, dict):
                # Handle nested navigation groups
                result.append(format_navigation([page], depth + 1, keywords))
            else:
                # Handle individual pages
                result.append(format_page_entry(page, indent, keywords))

    ret_val = "\n".join(result)
    ret_val = ret_val.replace("- Home\n", "- [Home](index.md)\n")
    return ret_val


def add_api_ref_to_mkdocs_template(mkdocs_nav: str, section_to_follow: str) -> str:
    """Add API Reference section to the navigation template."""
    api_reference_section = """- API References
{api}
"""
    section_to_follow_marker = f"- {section_to_follow}"

    replacement_content = f"{api_reference_section}{section_to_follow_marker}"
    ret_val = mkdocs_nav.replace(section_to_follow_marker, replacement_content)
    return ret_val


@require_optional_import("jinja2", "docs")
def generate_mkdocs_navigation(website_dir: Path, mkdocs_root_dir: Path, nav_exclusions: list[str]) -> None:
    mintlify_nav_template_path = website_dir / "mint-json-template.json.jinja"
    mkdocs_nav_path = mkdocs_root_dir / "docs" / "navigation_template.txt"
    summary_md_path = mkdocs_root_dir / "docs" / "SUMMARY.md"

    mintlify_json = json.loads(Template(mintlify_nav_template_path.read_text(encoding="utf-8")).render())
    mintlify_nav = mintlify_json["navigation"]
    filtered_nav = [item for item in mintlify_nav if item["group"] not in nav_exclusions]

    mkdocs_nav = format_navigation(filtered_nav)
    mkdocs_nav_with_api_ref = add_api_ref_to_mkdocs_template(mkdocs_nav, "Contributor Guide")

    mkdocs_nav_content = "---\nsearch:\n  exclude: true\n---\n" + mkdocs_nav_with_api_ref + "\n"
    mkdocs_nav_path.write_text(mkdocs_nav_content)
    summary_md_path.write_text(mkdocs_nav_content)


def copy_assets(website_dir: Path) -> None:
    src_dir = website_dir / "static" / "img"
    dest_dir = website_dir / "mkdocs" / "docs" / "assets" / "img"

    git_tracket_img_files = get_git_tracked_and_untracked_files_in_directory(website_dir / "static" / "img")
    copy_files(src_dir, dest_dir, git_tracket_img_files)


def main() -> None:
    root_dir = Path(__file__).resolve().parents[2]
    website_dir = root_dir / "website"

    mint_input_dir = website_dir / "docs"

    mkdocs_root_dir = website_dir / "mkdocs"
    mkdocs_output_dir = mkdocs_root_dir / "docs" / "docs"

    if mkdocs_output_dir.exists():
        shutil.rmtree(mkdocs_output_dir)

    exclusion_list = [
        "docs/_blogs",
        "docs/.gitignore",
        "docs/use-cases",
        "docs/installation",
        "docs/user-guide/getting-started",
        "docs/user-guide/models/litellm-with-watsonx.md",
        "docs/contributor-guide/Migration-Guide.md",
    ]
    nav_exclusions = ["Use Cases"]

    files_to_copy = get_git_tracked_and_untracked_files_in_directory(mint_input_dir)
    filtered_files = filter_excluded_files(files_to_copy, exclusion_list, website_dir)

    copy_assets(website_dir)
    process_and_copy_files(mint_input_dir, mkdocs_output_dir, filtered_files)
    generate_mkdocs_navigation(website_dir, mkdocs_root_dir, nav_exclusions)
