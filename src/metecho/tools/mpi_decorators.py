import logging
from functools import wraps

logger = logging.getLogger(__name__)

logger.debug("Importing MPI")
try:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
except ImportError:
    logger.debug("MPI import failed: reverting to one process")

    class COMM_WORLD:
        rank = 0
        size = 1

    comm = COMM_WORLD()


def MPI_target_arg(arg_index):
    """Decorates the target function to parallelize over a single input iterable
    positional argument identified by the given index.

    If MPI is enabled and `MPI_root >= 0` it gathers the results into the `MPI_root`
    process and removes them from the calculating processes.
    If the results needs to be broadcast that can be done after calling the function.

    :param arg_index int: Index of the positional argument to iterate over.

    The wrapped function gain the following parameters:
    :MPI bool: Flag that enables MPI if `true`, defaults to `false`.
    :MPI_root int: Rank of the process to gather iteration results in, defaults to 0.
    If set to a negative number, no gathering is performed.
    """

    def _mpi_wrapper(func):
        @wraps(func)
        def _mpi_wrapped_func(*args, **kwargs):
            input_list = args[arg_index]
            _args = list(args)
            rets = [None] * len(input_list)

            MPI = kwargs.pop("MPI", False)
            root = kwargs.pop("MPI_root", 0)

            if MPI:
                iter_inds = range(comm.rank, len(input_list), comm.size)
            else:
                iter_inds = range(len(input_list))

            for ind in iter_inds:
                _args[arg_index] = input_list[ind]
                rets[ind] = func(*_args, **kwargs)

            if MPI and root is None:
                pass
            elif MPI and root >= 0:
                if comm.rank == root:
                    for thr_id in range(comm.size):
                        if thr_id == root:
                            continue

                        mpi_inds = range(thr_id, len(input_list), comm.size)
                        for ind in mpi_inds:
                            rets[ind] = comm.recv(source=thr_id, tag=ind)
                else:
                    for ind in iter_inds:
                        comm.send(rets[ind], dest=root, tag=ind)

                if comm.rank != root:
                    for ind in iter_inds:
                        rets[ind] = None
            elif MPI and root < 0:
                for ind in iter_inds:
                    rets[ind] = comm.bcast(rets[ind], root=comm.rank)

            return rets

        return _mpi_wrapped_func

    return _mpi_wrapper
