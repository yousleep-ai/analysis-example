"""
A minimal example of an analysis script that interfaces with the youSleep Portal.
"""

# Import inbuilt packages
import logging
import json
import math
from typing import List
from argparse import ArgumentParser

# Import third-party packages
import mne

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

    # Custom parameters
    parser.add_argument(
        "--staging-window-length-ms",
        type=int,
        default=30000,
        choices=[15000, 30000, 60000],
        help="Length of the staging window in seconds.",
    )

    return parser.parse_args()


def create_event(label: str, start_ms: int, end_ms: int, channels: List[str]) -> dict:
    """
    Returns an event dictionary with the given label, start and end times.
    """
    return {
        "start_time_ms": start_ms,  # Start time of the event in milliseconds
        "end_time_ms": end_ms,  # End time of the event in milliseconds
        "label": label,  # Valid EDF+ label (e.g., 'Sleep stage ?')
        "channels": channels,  # Optional channel names the event refers to. Empty == all channels.
        # "probability": None,     # If a probabilistic event, a float in [0, 1] representing the probability.
        # "value": None,           # If a valued event, a float representing the value.
    }


def main():
    """
    The main analysis function which does roughly the following:
    1. Parse the arguments.
    2. Load the EDF file.
    3. Writes 'Sleep stage ?' events of length equal to the staging window length to the output
       JSON file.
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
    n_windows = math.ceil(length_ms / args.staging_window_length_ms)
    logger.info("Number of staging windows: %d", n_windows)
    logger.info("Length of recording: %d ms", length_ms)

    # Create events
    logger.info("Creating events")
    events = []
    for epoch_index in range(n_windows):
        start_ms = epoch_index * args.staging_window_length_ms
        end_ms = min(start_ms + args.staging_window_length_ms, length_ms)
        event = create_event("Sleep stage ?", start_ms, end_ms, args.channel_names)
        events.append(event)

    # Write events to output file
    logger.info("Saving %d events to %s", len(events), args.output_file)
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4)


if __name__ == "__main__":
    main()
