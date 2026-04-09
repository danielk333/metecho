import argparse
import logging
import sys
from typing import Callable

try:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
except ImportError:

    class COMM_WORLD:
        rank = 0
        size = 1

    comm = COMM_WORLD()

from ..tools import profiling

logger = logging.getLogger(__name__)

COMMANDS: dict[str, dict] = dict()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Radar meteor echo analysis toolbox")

    parser.add_argument("-p", "--profiler", action="store_true", help="Run profiler")
    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="count", default=0)

    subparsers = parser.add_subparsers(help="Avalible command line interfaces", dest="command")
    subparsers.required = True

    for name, dat in COMMANDS.items():
        parser_builder, command_help = dat["parser"]
        cmd_parser = subparsers.add_parser(name, help=command_help)
        parser_builder(cmd_parser)

    return parser


def add_command(
    name: str,
    function: Callable,
    parser_build: Callable[[argparse.ArgumentParser], argparse.ArgumentParser],
    add_parser_args: dict[str, str] = {},
) -> None:
    """
    Add a new command.
    Used by CLI scripts in order register new commands

    Args:
        name: Name of command
        function: Function to execute
        parser_build: Available parser that should be added as a subparser
        add_parser_args: parser arguments

    """
    COMMANDS[name] = dict()
    COMMANDS[name]["function"] = function
    COMMANDS[name]["parser"] = (parser_build, add_parser_args)


def main() -> None:

    parser = build_parser()
    args = parser.parse_args()

    handler = logging.StreamHandler(sys.stdout)
    if comm.size > 1:
        formatter = logging.Formatter(f"RANK{comm.rank} - %(asctime)s %(levelname)s %(name)s - %(message)s")
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    handler.setFormatter(formatter)

    lib_logger = logging.getLogger("metecho")
    if args.verbose > 0:
        lib_logger.addHandler(handler)
        lib_logger.setLevel(logging.INFO)
    else:
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

    if args.verbose > 1:
        logger.info("Logging level set to debug")
        lib_logger.setLevel(logging.DEBUG)

    if args.profiler:
        profiling.profile()

    function = COMMANDS[args.command]["function"]
    logger.info(f"Executing command {args.command}")

    function(args)

    if args.verbose > 0 and args.profiler:
        stats, total = profiling.get_profile()
        profiling.print_profile(stats, total=total)
        profiling.profile_stop()
