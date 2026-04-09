# This is needed so that the registration is performed
from . import cmd_plot, event_search

# Then expose the main after registration
from .commands import main
