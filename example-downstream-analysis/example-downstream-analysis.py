"""
A minimal example of a downstream analysis that interfaces with the youSleep Portal.

A downstream analysis depends on the events of another analysis. The portal
invokes it with one argument, ``--manifest-file``; the manifest names the
recording, the upstream events document (``inputs.events``) and the output
path as the container sees them. This example writes one "EEG arousal" event
wherever the upstream document has a "Sleep stage ?" event.
"""

# Import inbuilt packages
import logging
from argparse import ArgumentParser
from pathlib import Path

# Import third-party packages
import mne
from yousleep_common.models.events import Event
from yousleep_common.utils.event_blocks import (
    blocks_to_events,
    load_events_output,
    save_event_blocks,
)
from yousleep_common.utils.manifest import load_manifest

# Define module logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse the one argument the portal passes."""
    parser = ArgumentParser(
        description="A minimal example of a downstream analysis script that interfaces "
        "with the youSleep Portal."
    )
    parser.add_argument(
        "--manifest-file",
        type=Path,
        required=True,
        help="The analysis manifest written by the portal (or by `yousleep-manifest` "
        "for a hand run; give it --events-path).",
    )
    return parser.parse_args()


def create_event(label: str, start_ms: int, end_ms: int, channels: list[str]) -> Event:
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
    1. Read the manifest.
    2. Load the EDF file and validate its length matches the upstream events.
    3. Write 'EEG arousal' events wherever the upstream document has 'Sleep stage ?' events.
    """
    args = parse_args()
    manifest = load_manifest(args.manifest_file)
    logger.info(
        "Running %s for analysis %s with parameters %s",
        manifest.analysis.config_id,
        manifest.analysis.id,
        manifest.parameters,
    )
    if manifest.inputs.events is None:
        raise ValueError(
            "This analysis needs upstream events; the manifest names none "
            "(the configuration must declare an events input)."
        )

    # Read the EDF file the manifest names
    recording = manifest.inputs.recording
    logger.info("Reading EDF file %s...", recording.path)
    edf_file = mne.io.read_raw_edf(recording.path, preload=False)
    sampling_rate = edf_file.info["sfreq"]
    channel_names = [channel.name for channel in recording.channels]

    n_samples = edf_file.n_times
    length_ms = int(n_samples / sampling_rate * 1000)

    # Load the upstream events. `load_events_output` accepts every schema the
    # platform has ever written -- the block document and the legacy event
    # lists -- and returns one canonical document either way.
    logger.info("Loading upstream events from %s...", manifest.inputs.events.path)
    events = blocks_to_events(load_events_output(manifest.inputs.events.path).blocks)

    # Check that the last event ends at the end of the recording
    last_event = max(events, key=lambda e: e.end_time_ms)
    if last_event.end_time_ms != length_ms:
        raise ValueError(
            f"Last event ends at {last_event.end_time_ms} ms, but the recording ends "
            f"at {length_ms} ms."
        )

    # Create 'EEG arousal' events matching the 'Sleep stage ?' events
    logger.info("Creating 'EEG arousal' events...")
    arousal_events = [
        create_event("EEG arousal", event.start_time_ms, event.end_time_ms, channel_names)
        for event in events
    ]

    # Write the events output document (block-encoded on the way out, gzip on a
    # .gz suffix: the artifact stored on S3 is byte-identical to this file).
    output_path = Path(manifest.outputs.events.path)
    logger.info("Saving %d events to %s", len(arousal_events), output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_event_blocks(output_path, arousal_events)


if __name__ == "__main__":
    main()
