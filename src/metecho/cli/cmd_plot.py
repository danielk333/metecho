import argparse
import logging
from pathlib import Path

from metecho.data_handling.load_events import load_events

from .commands import add_command

logger = logging.getLogger(__name__)


def main(args: argparse.Namespace) -> None:

    load_events(Path(args.file))


def parser_build(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Adds mandatory and optional positional arguments to the parser."""

    parser.add_argument(
        "file",
        help="Input the location of the file to plot.",
    )
    return parser


add_command(
    name="plot",
    function=main,
    parser_build=parser_build,
    # command_help="Searches radar data to look for signs of meteor events.",
)
