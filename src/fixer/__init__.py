"""
Fix Hugo markdown files (turn them into Org mode files).

Using frontmatter to parse the front matter, mistletoe as markdown
parser and writing a simple OrgMode renderer
"""

import frontmatter
import click
from mistletoe.base_renderer import BaseRenderer
from mistletoe import Document, block_token, span_token
from pathlib import Path


class OrgRenderer(BaseRenderer):
    """A renderer for org mode."""

    def __init__(self, metadata: dict, extras, kwargs):
        """Initialize the renderer."""
        self.metadata = metadata
        super().__init__(extras, kwargs)

    def render_raw_text(self, token) -> str:
        """
        Default render method for RawText. Simply return token.content.
        """
        return token.content

    def render_strong(self, token: span_token.Strong) -> str:
        """Render bold."""
        return self.render_inner(token)

    def render_emphasis(self, token: span_token.Emphasis) -> str:
        """Render emph."""
        return self.render_inner(token)

    def render_inline_code(self, token: span_token.InlineCode) -> str:
        """Render inline code."""
        return self.render_inner(token)

    def render_strikethrough(self, token: span_token.Strikethrough) -> str:
        """Render strikethrough."""
        return self.render_inner(token)

    def render_image(self, token: span_token.Image) -> str:
        """Render image link."""
        return self.render_inner(token)

    def render_link(self, token: span_token.Link) -> str:
        """Render link."""
        return self.render_inner(token)

    def render_auto_link(self, token: span_token.AutoLink) -> str:
        """Render link."""
        return self.render_inner(token)

    def render_escape_sequence(self, token: span_token.EscapeSequence) -> str:
        """Render scape sequence."""
        return self.render_inner(token)

    def render_line_break(self, token: span_token.LineBreak) -> str:
        """Render line break."""
        return self.render_inner(token)

    def render_heading(self, token: block_token.Heading) -> str:
        """Render headings."""
        return self.render_inner(token)

    def render_quote(self, token: block_token.Quote) -> str:
        """Render quotes."""
        return self.render_inner(token)

    def render_paragraph(self, token: block_token.Paragraph) -> str:
        """Render paragram."""
        return self.render_inner(token)

    def render_block_code(self, token: block_token.BlockCode) -> str:
        """Render code block."""
        return self.render_inner(token)

    def render_list(self, token: block_token.List) -> str:
        """Render list."""
        return self.render_inner(token)

    def render_list_item(self, token: block_token.ListItem) -> str:
        """Render list item."""
        return self.render_inner(token)

    def render_table(self, token: block_token.Table) -> str:
        """Render table."""
        return self.render_inner(token)

    def render_table_cell(self, token: block_token.TableCell) -> str:
        """Render table cell."""
        return self.render_inner(token)

    def render_table_row(self, token: block_token.TableRow) -> str:
        """Render table row"""
        return self.render_inner(token)

    def render_thematic_break(self, token: block_token.ThematicBreak) -> str:
        """Render whatever this is."""
        return self.render_inner(token)



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
        matter = frontmatter.load(filename)
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
