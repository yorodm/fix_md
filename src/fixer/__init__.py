"""
Fix Hugo markdown files (turn them into Org mode files).

Using frontmatter to parse the front matter, mistletoe as markdown
parser and writing a simple OrgMode renderer
"""

import frontmatter
import click
from mistletoe.base_renderer import BaseRenderer
from mistletoe import Document
from pathlib import Path


class OrgRenderer(BaseRenderer):
    """A renderer for org mode."""

    def __init__(self, metadata: dict, extras, kwargs):
        """Initialize the renderer."""
        self.metadata = metadata
        super().__init__(extras, kwargs)


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
