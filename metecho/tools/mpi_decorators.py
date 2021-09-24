import copy
import logging

logger = logging.getLogger(__name__)

logger.debug('Importing MPI')
try:
    from mpi4py import MPI
    comm = MPI.COMM_WORLD
except ImportError:
    logger.warning('MPI import failed: reverting to one process')
    class COMM_WORLD:
        rank = 1
        size = 1
    comm = COMM_WORLD()


def MPI_target_arg(arg_index):
    '''Decorates the target function to parallelize over a single input iterable positional argument identified by the given index.
    '''
    def _mpi_wrapper(func):
        def _mpi_wrapped_func(*args, **kwargs):

            rets = []
            input_list = args[arg_index]
            _args = copy.copy(args)

            for item in input_list:
                _args[arg_index] = item
                ret = func(*_args, **kwargs)

                rets.append(ret)

            return rets

        return _mpi_wrapped_func
    return _mpi_wrapper
