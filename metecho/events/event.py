import datetime


class Event:
    """Stores events created in event_search to be passed on for later use"""
    start_IPP = []
    end_IPP = []
    found_indices = []
    date = ""
    file_start_t = ""
    files = []
    tstart = ""
    event_search_executed = ""
    event_search_config = {}
    data = []
    event_type = ""
    noise = {}

    def __init__(self, data):
        self.data = data
