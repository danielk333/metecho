import logging
from pathlib import Path
import os

from .. import data
from .commands import add_command

logger = logging.getLogger(__name__)

try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
except ImportError:
    class COMM_WORLD:
        rank = 0
        size = 1
    
        def barrier(self):
            pass

    comm = COMM_WORLD()


def main(args, cli_logger):
    if args.list:
        print(data.list_converters())
        cli_logger.info('Listing complete, exiting...')
        return
    if len(args.files) == 0:
        cli_logger.info('No input paths, exiting...')

    output_dir = Path(args.output).resolve()
    paths = []
    converted_count = 0
    for path in args.files:
        path = Path(path).resolve()
        if path.is_dir():
            data_store = data.DataStore(
                path, 
                include_convertable = True,
            )
            converted = data_store.convert(output_dir, args.backend, MPI=comm.size > 1)
            
            for sub_pth in converted:
                converted_count += len(sub_pth)
                for pth in sub_pth:
                    logger.info(f'Generated [{args.backend}] {pth}')
        else:
            paths.append(path)

    converted = data.convert(paths, output_dir, args.backend, MPI=comm.size > 1)
    converted_count += len(converted)
    for sub_pth in converted:
        converted_count += len(sub_pth)
        for pth in sub_pth:
            logger.info(f'Generated [{args.backend}] {pth}')

    cli_logger.info(f'Conversion complete: {converted_count} files generated')


def parser_build(parser):
    parser.add_argument(
        "-b", "--backend",
        default=None,
        help="Target backend format to convert to",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List avalible convertable formats and target backends",
    )
    parser.add_argument(
        "files",
        nargs='*',
        default=[],
        help="Input the locations of the files (or folders) to be converted",
    )
    parser.add_argument(
        "-o", "--output",
        default=str(Path(os.getcwd()).resolve()),
        help="The output location of the converted files",
    )

    return parser


add_command(
    name='convert',
    function=main,
    parser_build=parser_build,
    command_help='Convert the target files to a supported backend format',
)
