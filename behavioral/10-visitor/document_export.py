from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import List, Protocol


class DocumentVisitor(Protocol):
    """Protocol for document export visitors."""

    def visit_paragraph(self, paragraph: "Paragraph") -> None: ...
    def visit_code_block(self, code_block: "CodeBlock") -> None: ...
    def visit_image(self, image: "Image") -> None: ...
    def visit_table(self, table: "Table") -> None: ...
    def visit_heading(self, heading: "Heading") -> None: ...
    def get_result(self) -> str: ...
    def reset(self) -> None: ...


class DocumentElement(Protocol):
    """Protocol for document elements."""

    def accept(self, visitor: DocumentVisitor) -> None: ...


@dataclass(frozen=True)
class Paragraph:
    """Represents a paragraph of text."""

    text: str

    def accept(self, visitor: DocumentVisitor) -> None:
        visitor.visit_paragraph(self)


@dataclass(frozen=True)
class CodeBlock:
    """Represents a code block with syntax highlighting."""

    language: str
    code: str

    def accept(self, visitor: DocumentVisitor) -> None:
        visitor.visit_code_block(self)


@dataclass(frozen=True)
class Image:
    """Represents an image with alt text."""

    src: str
    alt_text: str

    def accept(self, visitor: DocumentVisitor) -> None:
        visitor.visit_image(self)


@dataclass(frozen=True)
class Table:
    """Represents a table with headers and rows."""

    headers: List[str]
    rows: List[List[str]] = field(default_factory=list)

    def __post_init__(self):
        if not self.headers:
            raise ValueError("Table must have at least one header")
        for row in self.rows:
            if len(row) != len(self.headers):
                raise ValueError("All rows must have same number of columns as headers")

    def accept(self, visitor: DocumentVisitor) -> None:
        visitor.visit_table(self)


@dataclass(frozen=True)
class Heading:
    """Represents a heading with level (1-6)."""

    text: str
    level: int = 1

    def __post_init__(self):
        if not 1 <= self.level <= 6:
            raise ValueError("Heading level must be between 1 and 6")

    def accept(self, visitor: DocumentVisitor) -> None:
        visitor.visit_heading(self)


class Document:
    """Represents a document containing multiple elements."""

    def __init__(self, elements: List[DocumentElement]) -> None:
        self.elements = elements

    def export(self, visitor: DocumentVisitor) -> str:
        """Export document using the provided visitor."""
        visitor.reset()
        for element in self.elements:
            element.accept(visitor)
        return visitor.get_result()


class HTMLExportVisitor:
    """Exports documents to HTML format with proper escaping."""

    def __init__(self) -> None:
        self.parts: List[str] = []

    def visit_paragraph(self, paragraph: Paragraph) -> None:
        escaped_text = html.escape(paragraph.text)
        self.parts.append(f"<p>{escaped_text}</p>")

    def visit_code_block(self, code_block: CodeBlock) -> None:
        escaped_code = html.escape(code_block.code)
        self.parts.append(
            f'<pre><code class="language-{code_block.language}">{escaped_code}</code></pre>'
        )

    def visit_image(self, image: Image) -> None:
        escaped_src = html.escape(image.src)
        escaped_alt = html.escape(image.alt_text)
        self.parts.append(f'<img src="{escaped_src}" alt="{escaped_alt}" />')

    def visit_table(self, table: Table) -> None:
        escaped_headers = [html.escape(h) for h in table.headers]
        header_html = "".join(f"<th>{h}</th>" for h in escaped_headers)

        rows_html = ""
        for row in table.rows:
            escaped_cells = [html.escape(cell) for cell in row]
            rows_html += (
                "<tr>" + "".join(f"<td>{cell}</td>" for cell in escaped_cells) + "</tr>"
            )

        self.parts.append(
            f"<table><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table>"
        )

    def visit_heading(self, heading: Heading) -> None:
        escaped_text = html.escape(heading.text)
        self.parts.append(f"<h{heading.level}>{escaped_text}</h{heading.level}>")

    def get_result(self) -> str:
        return "\n".join(self.parts)

    def reset(self) -> None:
        """Reset visitor state for reuse."""
        self.parts = []


class MarkdownExportVisitor:
    """Exports documents to Markdown format."""

    def __init__(self) -> None:
        self.parts: List[str] = []

    def visit_paragraph(self, paragraph: Paragraph) -> None:
        self.parts.append(paragraph.text + "\n")

    def visit_code_block(self, code_block: CodeBlock) -> None:
        self.parts.append(f"```{code_block.language}\n{code_block.code}\n```\n")

    def visit_image(self, image: Image) -> None:
        self.parts.append(f"![{image.alt_text}]({image.src})\n")

    def visit_table(self, table: Table) -> None:
        header_line = "| " + " | ".join(table.headers) + " |"
        separator_line = "| " + " | ".join("---" for _ in table.headers) + " |"
        rows_lines = "\n".join("| " + " | ".join(row) + " |" for row in table.rows)
        self.parts.append(f"{header_line}\n{separator_line}\n{rows_lines}\n")

    def visit_heading(self, heading: Heading) -> None:
        prefix = "#" * heading.level
        self.parts.append(f"{prefix} {heading.text}\n")

    def get_result(self) -> str:
        return "\n".join(self.parts)

    def reset(self) -> None:
        """Reset visitor state for reuse."""
        self.parts = []


class LaTeXExportVisitor:
    """Exports documents to LaTeX format."""

    def __init__(self) -> None:
        self.parts: List[str] = []

    def visit_paragraph(self, paragraph: Paragraph) -> None:
        escaped = paragraph.text.replace("\\", "\\textbackslash{}").replace("_", "\\_")
        self.parts.append(f"{escaped}\n")

    def visit_code_block(self, code_block: CodeBlock) -> None:
        self.parts.append(
            f"\\begin{{lstlisting}}[language={code_block.language}]\n"
            f"{code_block.code}\n"
            f"\\end{{lstlisting}}\n"
        )

    def visit_image(self, image: Image) -> None:
        self.parts.append(
            f"\\begin{{figure}}[h]\n"
            f"\\centering\n"
            f"\\includegraphics{{{image.src}}}\n"
            f"\\caption{{{image.alt_text}}}\n"
            f"\\end{{figure}}\n"
        )

    def visit_table(self, table: Table) -> None:
        col_spec = "c" * len(table.headers)
        header = " & ".join(table.headers) + " \\\\"
        rows = "\n".join(" & ".join(row) + " \\\\" for row in table.rows)

        self.parts.append(
            f"\\begin{{table}}[h]\n"
            f"\\centering\n"
            f"\\begin{{tabular}}{{{col_spec}}}\n"
            f"\\hline\n"
            f"{header}\n"
            f"\\hline\n"
            f"{rows}\n"
            f"\\hline\n"
            f"\\end{{tabular}}\n"
            f"\\end{{table}}\n"
        )

    def visit_heading(self, heading: Heading) -> None:
        levels = ["section", "subsection", "subsubsection", "paragraph", "subparagraph"]
        level_name = levels[min(heading.level - 1, len(levels) - 1)]
        self.parts.append(f"\\{level_name}{{{heading.text}}}\n")

    def get_result(self) -> str:
        return "\n".join(self.parts)

    def reset(self) -> None:
        """Reset visitor state for reuse."""
        self.parts = []


def demo_document_export():
    """Demonstrate the document export example."""
    doc = Document(
        [
            Heading("User Guide", level=1),
            Paragraph("Welcome to our documentation system."),
            Heading("Getting Started", level=2),
            Paragraph("Follow these steps to begin:"),
            CodeBlock("python", "def hello():\n    print('Hello, World!')"),
            Image("diagram.png", "System Architecture"),
            Table(
                headers=["Feature", "Status", "Priority"],
                rows=[
                    ["Export HTML", "Done", "High"],
                    ["Export Markdown", "Done", "High"],
                    ["Export LaTeX", "Done", "Medium"],
                ],
            ),
        ]
    )

    # HTML Export
    print("\nHTML Export:")
    print("-" * 70)
    html_visitor = HTMLExportVisitor()
    print(doc.export(html_visitor))

    # Markdown Export
    print("\nMarkdown Export:")
    print("-" * 70)
    markdown_visitor = MarkdownExportVisitor()
    print(doc.export(markdown_visitor))

    # LaTeX Export
    print("\nLaTeX Export:")
    print("-" * 70)
    latex_visitor = LaTeXExportVisitor()
    print(doc.export(latex_visitor))


def main():
    """Run all demonstrations."""
    demo_document_export()


if __name__ == "__main__":
    main()
