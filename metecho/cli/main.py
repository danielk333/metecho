import argparse
import sys
import logging

from ..tools import PROFILER as profiler

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Radar meteor echo analysis toolbox')

parser.add_argument('-p', '--profiler', action='store_true', help='Run profiler')
parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='count', default=0)

subparsers = parser.add_subparsers(dest='command')

COMMANDS = dict()


def add_command(name, function, command_help=''):
    global COMMANDS

    subparsers.add_parser(name, help=command_help)
    COMMANDS[name] = function
    return subparsers


def main():

    args = parser.parse_args()

    handler = logging.StreamHandler(sys.stdout)

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

    function = COMMANDS[args.command]
    logger.info(f'Executing command {args.command}')

    function(args, logger)

    if args.verbose > 0 and args.profiler:
        profiler.stop('full')
        logger.info(profiler)
