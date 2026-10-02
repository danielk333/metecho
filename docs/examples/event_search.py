# # Event Search

# ##Prerequisites
# ---

import os
import sys
import tempfile
from pathlib import Path

from radardef.radar_stations import Mu

from metecho import event_search
from metecho.plot.event_search import plot_events

# Workaround to make jupyter notebook find utils
sys.path.insert(1, str(Path(os.path.abspath("")) / "docs" / "examples" / "extras"))
import utils

# Download data and convert to a compatible format, in this case we are working with a MUI file

tmp_dir = tempfile.TemporaryDirectory()
raw_path = Path(tmp_dir.name) / "raw"
raw_path.mkdir(parents=True, exist_ok=True)
converted_path = Path(tmp_dir.name) / "converted"
raw_data = utils.download_test_data(raw_path)
data_path = utils.convert_test_data(raw_data, converted_path)[0]

# ## Event Search
# ---

# Here we run the event search. The event search is utilizing the **hardtarget** analyse function
# to run a echo search, from this analysis we process the data to extract events. In this case we
# do not specify a custom configuration file, we let the tool generate one automatically from the
# experiment definition. The experiment definition is extracted from parameters in the MUI file
# but can be overriden if wanted, see event search for more information.

data = Mu().load_data(data_path)
events, echo, noise = event_search(data=data)

# The results can then be analysed further visually

plot_events(echo, events, data)
