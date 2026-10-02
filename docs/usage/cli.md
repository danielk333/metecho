# CLI

The Command Line Interface of metecho is exposed under a single executable **metecho**.

```bash
    metecho -h
```

The **metecho** executable provides access to 2 tools right now, more to come.

---

## event_search

Use the **event_search** to analyse a data file of radar data and extract meteor and meteor trail events.
Supported for any data supported by [radardef](https://pypi.org/project/radardef/), if not yet available in radardef contact the responsible developers. This tool supports plotting if using the correct flag.

```bash
    $ metecho event_search -h
    $ metecho event_search <path/to/data> --plot --progress --impl c --config <path/to/config.ini>
```

---

## Plot

Use the **plot** tool to plot a already analysed event search file, **plot**. At this time the raw data will not be visible if plotting after analysis.

```bash
    $ hardtarget plot -h
    $ hardtarget plot <path/to/event_search_file>
```

---
