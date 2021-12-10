import datetime


class Event:
    """Stores events created in event_search to be passed on for later use"""

    def __init__(self, data):
        self.data = data
        self.start_IPP = []
        self.end_IPP = []
        self.found_indices = []
        self.date = ""
        self.file_start_t = ""
        self.files = []
        self.tstart = ""
        self.event_search_executed = ""
        self.event_search_config = {}
        self.data = []
        self.event_type = ""
        self.noise = {}
