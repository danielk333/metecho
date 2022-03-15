import logging
import sys

from .profiling import PROFILER

file_logger = logging.getLogger(__name__)


def debug():
    handler = logging.StreamHandler(sys.stdout)
    logger = logging.getLogger('metecho')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    PROFILER.enable('metecho')
