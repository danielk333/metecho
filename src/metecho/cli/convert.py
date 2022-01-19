from .. import data
from .. import tools
from .main import add_command


def main(args, cli_logger):
    cli_logger.info('THIS IS THE CONVERTER FUNCTION')


parser = add_command(
    name='convert',
    function=main,
    command_help='Convert the target files to a supported backend format',
)

parser.add_argument("files", nargs='+',
                    help="Input the locations of the files (or folders) you want analyzed.")
parser.add_argument("output",
                    help="The output location of the converted files")
