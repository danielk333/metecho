import datetime


class Event:
    """Stores events created in event_search to be passed on for later use"""

    def __init__(self, start_IPP, end_IPP, files, date, **kwargs):
        self.search_data = kwargs.pop('search_data', None)
        self.start_IPP = start_IPP
        self.end_IPP = end_IPP
        self.found_indices = kwargs.pop('found_indices', None)
        self.date = date
        self.files_start_date = kwargs.pop('files_start_date', None)
        self.files = files
        self.event_search_executed = kwargs.pop('event_search_executed', None)
        self.event_search_config = kwargs.pop('event_search_config', None)
        self.event_type = kwargs.pop('event_type', 'meteor')
        self.noise = kwargs.pop('noise', None)
