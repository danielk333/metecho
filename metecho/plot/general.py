import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

def basic_matplotlib_kw(func):
    '''Decorator that adds basic matplotlib figure functionality. 

    Assumes that wrapped function returns a matplotlib axes and takes an 
    matplotlib axes as its first argument. 
    Wrapped function returns a figure and axis tuple.
    '''

    def mpl_wrapped_func(*args, **kwargs):

        show_figure = kwargs.pop('show_figure', False)
        output_path = kwargs.pop('output_path', None)
        keep_figure = kwargs.pop('keep_figure', True)
        ax = kwargs.pop('ax', None)

        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
        else:
            fig = None

        ax = func(ax, *args, **kwargs)

        if output_path is not None:
            try:
                fig.savefig(output_path)
            except FileNotFoundError:
                logger.exception(f'Output path {output_path} directory does not exist.')
        if show_figure:
            plt.show()
        if not keep_figure:
            fig.close()

        return fig, ax

    return mpl_wrapped_func