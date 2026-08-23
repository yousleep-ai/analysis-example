"""
A minimal example of an analysis script that interfaces with the youSleep Portal.
"""

# Import inbuilt packages
import logging
from pathlib import Path
from typing import List
from argparse import ArgumentParser

# Import third-party packages
import mne
from yousleep_common.models.events import Event
from yousleep_common.utils.event_blocks import (
    blocks_to_events,
    load_events_output,
    write_event_blocks,
)

# Define module logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse the mandatory arguments & single custom --staging-window-length argument.
    """
    parser = ArgumentParser(
        description="A minimal example of an analysis script that interfaces with the "
        "youSleep Portal."
    )

    # The following arguments are mandatory and will always be passed to the analysis by the portal.
    # They must be handled by the analysis script even if not used.
    # See analysis config parameters.defaults field for a list of all required parameters.
    parser.add_argument("--input-file", type=str, help="Path to the input EDF file.")
    parser.add_argument(
        "--events-file", type=str, help="Path to the input events file."
    )
    parser.add_argument("--output-file", type=str, help="Path to the output JSON file.")
    parser.add_argument(
        "--channel-names", type=str, nargs="+", help="List of channel names."
    )
    parser.add_argument(
        "--channel-types",
        type=str,
        nargs="+",
        help="List of channel types (e.g., 'EEG', 'EOG').",
    )
    parser.add_argument(
        "--channel-units",
        type=str,
        nargs="+",
        help="List of channel units (e.g., 'uV').",
    )
    parser.add_argument(
        "--cpus", type=int, help="Number of CPUs available for parallel processing."
    )
    parser.add_argument("--memory-mib", type=int, help="Memory available in MiB.")

    return parser.parse_args()


def create_event(label: str, start_ms: int, end_ms: int, channels: List[str]) -> Event:
    """
    Returns an Event with the given label, start and end times.
    """
    return Event(
        start_time_ms=start_ms,
        end_time_ms=end_ms,
        label=label,  # Valid EDF+ label (e.g., 'EEG arousal')
        channels=channels,  # Optional channel names. Empty == all channels.
    )


def main():
    """
    The main analysis function which does roughly the following:
    1. Parse the arguments.
    2. Load the EDF file and validates its length matches the events file.
    3. Writes 'EEG arousal' events whereevere the events file has 'Sleep stage ?' events.
    """
    # Parse the arguments
    args = parse_args()
    logger.info("Running analysis with the following arguments: %s", vars(args))

    # Read the EDF file
    logger.info("Reading EDF file...")
    edf_file = mne.io.read_raw_edf(args.input_file, preload=False)
    sampling_rate = edf_file.info["sfreq"]

    # Compute how many epochs of 'staging_window_length' (seconds)
    n_samples = edf_file.n_times
    length_ms = int(n_samples / sampling_rate * 1000)

    # Load the input events. `load_events_output` accepts every schema the
    # platform has ever written -- the block document and the legacy event
    # lists -- and returns one canonical document either way.
    logger.info("Loading events...")
    events = blocks_to_events(load_events_output(args.events_file).blocks)

    # Check that the last event ends at the end of the recording
    last_event = max(events, key=lambda e: e.end_time_ms)
    if last_event.end_time_ms != length_ms:
        raise ValueError(
            f"Last event ends at {last_event.end_time_ms} ms, but the recording ends "
            f"at {length_ms} ms."
        )

    # Create 'EDF Arousal' events matching the 'Sleep stage ?' events
    logger.info("Creating 'EEG arousal' events...")
    arousal_events = []
    for event in events:
        arousal_event = create_event(
            "EEG arousal",
            event.start_time_ms,
            event.end_time_ms,
            args.channel_names,
        )
        arousal_events.append(arousal_event)

    # Write the events output document (block-encoded on the way out)
    logger.info("Saving %d events to %s", len(arousal_events), args.output_file)
    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_file, "w", encoding="utf-8") as f:
        write_event_blocks(arousal_events, f)


if __name__ == "__main__":
    main()
