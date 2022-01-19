import argparse
import sys
import logging

try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
except ImportError:
    class COMM_WORLD:
        rank = 0
        size = 1

    comm = COMM_WORLD()

from ..tools import PROFILER as profiler

logger = logging.getLogger(__name__)

COMMANDS = dict()


def build_parser():
    parser = argparse.ArgumentParser(description='Radar meteor echo analysis toolbox')

    parser.add_argument('-p', '--profiler', action='store_true', help='Run profiler')
    parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='count', default=0)

    subparsers = parser.add_subparsers(help='Avalible command line interfaces', dest='command')
    subparsers.required = True

    for name, dat in COMMANDS.items():
        parser_builder, command_help = dat['parser']
        cmd_parser = subparsers.add_parser(name, help=command_help)
        parser_builder(cmd_parser)

    return parser


def add_command(name, function, parser_build, command_help=''):
    global COMMANDS
    COMMANDS[name] = dict()
    COMMANDS[name]['function'] = function
    COMMANDS[name]['parser'] = (parser_build, command_help)


def main():

    parser = build_parser()
    args = parser.parse_args()

    handler = logging.StreamHandler(sys.stdout)
    if comm.size > 1:
        formatter = logging.Formatter(f'RANK{comm.rank} - %(asctime)s %(levelname)s %(name)s - %(message)s')
    else:
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s - %(message)s')
    handler.setFormatter(formatter)

    lib_logger = logging.getLogger('metecho')
    if args.verbose > 0:
        lib_logger.addHandler(handler)
        lib_logger.setLevel(logging.INFO)
    else:
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
    
    if args.verbose > 1:
        logger.info('Logging level set to debug')
        lib_logger.setLevel(logging.DEBUG)

    if args.profiler:
        profiler.init('full', True)
        profiler.start('full')
        profiler.enable('metecho')

    function = COMMANDS[args.command]['function']
    logger.info(f'Executing command {args.command}')

    function(args, logger)

    if args.verbose > 0 and args.profiler:
        profiler.stop('full')
        logger.info('\n' + str(profiler))
