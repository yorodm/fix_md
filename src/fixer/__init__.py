"""
Fix Hugo markdown files (turn them into Org mode files).

Using frontmatter to parse the front matter, mistletoe as markdown
parser and writing a simple OrgMode renderer
"""
import re
import frontmatter
import click
from mistletoe.base_renderer import BaseRenderer
from mistletoe import Document, block_token, span_token
from pathlib import Path


class FigureTag(span_token.SpanToken):
    """Parse hugo style figure tag."""

    pattern = re.compile(r"{{<\s+figure src=\"*(.+?)\"\s+>}}")

    def __init__(self, match: re.Match):
        """Get the target from the match."""
        self.target = match.group(1)


class RefTag(span_token.SpanToken):
    """Parse hugo ref tag."""

    pattern = re.compile(r"\[*(.+?)\]\({{<\s*ref\s+\"*(.+?)\"\s*>}}\)")

    def __init__(self, match: re.Match):
        """Get the target from the match."""
        self.title = match.group(1)
        self.target = match.group(2)


class RelRefTag(RefTag):
    """Parse hugo relref tag."""

    pattern = re.compile(r"\[*(.+?)\]\({{<\s*relref \"*(.+?)\"\s*>}}\)")

    def __init__(self, match: re.Match):
        """Get the target from the match."""
        super().__init__(match)


class OrgRenderer(BaseRenderer):
    """A renderer for org mode."""

    def __init__(self, metadata: dict):
        """Initialize the renderer."""
        self.metadata = metadata
        super().__init__(FigureTag, RelRefTag, RefTag)

    def render_raw_text(self, token) -> str:
        """Render method for RawText. Simply return token.content."""
        return token.content

    def render_strong(self, token: span_token.Strong) -> str:
        """Render bold."""
        return "*" + self.render_inner(token) + "*"

    def render_emphasis(self, token: span_token.Emphasis) -> str:
        """Render emph."""
        return self.render_inner(token)

    def render_inline_code(self, token: span_token.InlineCode) -> str:
        """Render inline code."""
        return "~" + self.render_inner(token) + "~"

    def render_strikethrough(self, token: span_token.Strikethrough) -> str:
        """Render strikethrough."""
        return self.render_inner(token)

    def render_image(self, token: span_token.Image) -> str:
        """Render image link."""
        return self.render_inner(token)

    def render_link(self, token: span_token.Link) -> str:
        """Render link."""
        title = self.render_inner(token)
        return f"[[{token.target}][{title}]]"

    def render_auto_link(self, token: span_token.AutoLink) -> str:
        """Render link."""
        return self.render_link(token)

    def render_escape_sequence(self, token: span_token.EscapeSequence) -> str:
        """Render scape sequence."""
        return self.render_inner(token)

    def render_line_break(self, token: span_token.LineBreak) -> str:
        """Render line break."""
        return ("\n" if not token.soft else " ")

    def render_heading(self, token: block_token.Heading) -> str:
        """Render headings."""
        output = [
            "*" * token.level,
            " ",
            self.render_inner(token),
            2 * "\n"  # Leave an empty line after headings
        ]
        return ''.join(output)

    def render_quote(self, token: block_token.Quote) -> str:
        """Render quotes."""
        return self.render_inner(token)

    def render_paragraph(self, token: block_token.Paragraph) -> str:
        """Render paragram."""
        # Add to line breaks so the org parser doesn't mix paragraphs
        output = ''.join([self.render_inner(token), 2 * "\n"])
        return output

    def render_block_code(self, token: block_token.BlockCode) -> str:
        """Render code block."""
        output = [
            "#+begin_src",
            f" {token.language}",
            "\n",
            self.render_inner(token),
            "#+end_src",
            2 * "\n"  # Leave an empty line after code blocks
        ]
        return ''.join(output)

    def render_list(self, token: block_token.List) -> str:
        """Render list."""
        return self.render_inner(token)

    def render_list_item(self, token: block_token.ListItem) -> str:
        """Render list item."""
        from pprint import pprint
        pprint(vars(token))
        output = [
            token.prepend * " ",
            "- ",
            self.render_inner(token)
        ]
        return ''.join(output)

    def render_table(self, token: block_token.Table) -> str:
        """Render table."""
        return self.render_inner(token)

    def render_table_cell(self, token: block_token.TableCell) -> str:
        """Render table cell."""
        return self.render_inner(token)

    def render_table_row(self, token: block_token.TableRow) -> str:
        """Render table row."""
        return self.render_inner(token)

    def render_thematic_break(self, token: block_token.ThematicBreak) -> str:
        """Render whatever this is."""
        return self.render_inner(token)

    def render_document(self, token: Document) -> str:
        """Render a document converting metadata to Org Mode directives."""
        title = self.metadata.get("title", "")
        date = self.metadata.get("date", None)
        author = self.metadata.get("author", None)
        output = [
            f"#+title: {title}",
            "\n",
            f"#+date: {date}" if date else "",
            "\n",
            f"#+author: {author}" if author else "",
            "\n",  # empty line after the preamble
            self.render_inner(token)
        ]
        prev = object()  # marker
        output = [prev := i for i in output if prev != i]
        return ''.join(output)

    def render_rel_ref_tag(self, token: RelRefTag) -> str:
        """Render Hugo rel ref."""
        return f"[[{token.target}][{token.title}]]"

    def render_ref_tag(self, token: RefTag) -> str:
        """Render Hufo ref."""
        return f"[[{token.target}][{token.title}]]"

    def render_figure_tag(self, token: FigureTag) -> str:
        """Render Hugo figure."""
        return f"[[{token.target}]]"


class Runner:
    """Run the fixer."""

    def __init__(self, input_dir: str, output_dir: str, clobber: bool):
        """Initialize the runner."""
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.clobber = clobber

    def run(self):
        """Run the fixer."""
        if not self.input_dir.exists():
            raise f"Source directory {self.input_dir} does not exist"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        for file in self.input_dir.rglob("*.md"):
            self.convert(file)

    def convert(self, path: Path):
        """
        Convert the file and create it on output directory.

        Parse the file frontmatter and content, and initialize the OrgRenderer
        Check for clobber before doing anything.
        """
        filename = path.name
        output = self.output_dir / (filename + ".org")
        if output.exists() and not self.clobber:
            return
        print(f"Converting ${path} into ${output}")
        matter = frontmatter.load(path)
        with OrgRenderer(matter.metadata) as renderer:
            doc = Document(matter.content)
            output.write_text(renderer.render(doc))


@click.command()
@click.option("--source", help="Source directory")
@click.option("--dest", help="Destination directory")
@click.option("--clobber", default=True, help="Overwrite files in destination")
def fix(source: str, dest: str, clobber: bool):
    """
    Fix all files in directory.

    Runs the fixer, taking all markdown files in `source`  and generating
    the corresponding org files `dest`.
    """
    runner = Runner(source, dest, clobber)
    runner.run()
