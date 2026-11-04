"""
The CLI Plot functionality,  gathers the plot functionality for both the analysed and raw format.
"""

import argparse
import logging

from hardtarget.types import ParserArgs, SubParser

from . import plot_event_search
from .commands import add_command

logger = logging.getLogger(__name__)

SOURCES = {
    "event-search": SubParser(
        main=plot_event_search.main,
        parser_build=plot_event_search.parser_build,
        parser_args=ParserArgs(
            description="Plot cluster ",
            usage="%(prog)s [options] path",
        ),
    ),
}


def parser_build(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Adds mandatory and optional positional arguments to the parser."""
    subparsers = parser.add_subparsers(help="resordan file types", dest="filetype")
    subparsers.required = True
    for source in SOURCES:
        cmd_parser = subparsers.add_parser(source, **SOURCES[source].parser_args)
        parser_builder = SOURCES[source].parser_build
        parser_builder(cmd_parser)
    return parser


def main(args: argparse.Namespace) -> None:
    """Plot CLI"""
    function = SOURCES[args.filetype].main
    logger.info(f"Executing command {args.command} {args.filetype}")
    function(args)


add_command(
    name="plot",
    function=main,
    parser_build=parser_build,
    add_parser_args=dict(
        description="Metecho plotting tools",
    ),
)
