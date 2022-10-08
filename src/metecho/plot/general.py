import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)


def basic_matplotlib_kw(subplot_shape=None):
    '''Decorator that adds basic matplotlib figure functionality.

    Assumes that wrapped function returns a matplotlib axes and takes a
    matplotlib axes as its first argument.
    Wrapped function returns a figure and axis tuple.
    '''

    if subplot_shape is None:
        subplot_shape = (1, 1)

    def mpl_decorator(func):
        def mpl_wrapped_func(*args, **kwargs):

            show_figure = kwargs.pop('show_figure', False)
            output_path = kwargs.pop('output_path', None)
            keep_figure = kwargs.pop('keep_figure', True)
            ax = kwargs.pop('ax', None)

            if ax is None:
                fig, ax = plt.subplots(*subplot_shape)
            else:
                fig = None

            ax, handles = func(ax, *args, **kwargs)

            if output_path is not None:
                try:
                    fig.savefig(output_path)
                except FileNotFoundError:
                    logger.exception(f'Output path {output_path} directory does not exist.')
            if show_figure:
                plt.show()
            if not keep_figure:
                fig.close()

            return fig, ax, handles
        return mpl_wrapped_func
    return mpl_decorator
