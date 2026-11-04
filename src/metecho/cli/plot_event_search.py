import argparse
from pathlib import Path

from hardtarget.plotting.load_data import load_analysed_data
from radardef.radar_def import RadarDef

from metecho.data_handling.load_data import load_events
from metecho.events.event_search import echo_post_process
from metecho.plot.event_search import plot_events


def parser_build(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Adds mandatory and optional positional arguments to the parser."""

    parser.add_argument("echo_path", help="path to echo data")
    parser.add_argument("event_path", help="path to event data")
    parser.add_argument("-d", "--data", default=None, type=str, help="path to the raw data")

    return parser


def main(args: argparse.Namespace) -> None:
    """Plot CLI"""

    plot(Path(args.echo_path), Path(args.event_path), Path(args.data) if args.data else None)


def plot(
    echo_path: Path,
    event_path: Path,
    data_path: Path | None = None,
) -> None:
    """Load and plot Cluster data"""

    out, exp, cfg, pro = load_analysed_data(  # type: ignore[var-annotated]
        data_dir=echo_path,
    )
    events = load_events(event_path)
    echo = echo_post_process(out, exp, events.config[1])

    if data_path:
        data = RadarDef().load_data(data_path)
    else:
        data = None

    plot_events(echo=echo, events=events, data=data)
