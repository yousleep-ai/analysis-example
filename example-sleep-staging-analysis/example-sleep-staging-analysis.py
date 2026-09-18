"""
A minimal example of an analysis that interfaces with the youSleep Portal.

The portal invokes an analysis container with one argument, ``--manifest-file``,
and nothing else. The manifest (``yousleep_common.models.AnalysisManifest``)
names the recording and the output path as the container sees them, the
channels selected for the run, the custom parameters typed as the analysis
configuration declared them, and the resources the run has. This example reads
it, reads the recording's length, and writes one "Sleep stage ?" event per
staging window in the block document the portal accepts.
"""

# Import inbuilt packages
import logging
import math
from argparse import ArgumentParser
from pathlib import Path

# Import third-party packages
import mne
from yousleep_common.models.events import Event
from yousleep_common.utils.event_blocks import save_event_blocks
from yousleep_common.utils.manifest import load_manifest

# Define module logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse the one argument the portal passes."""
    parser = ArgumentParser(
        description="A minimal example of an analysis script that interfaces with the "
        "youSleep Portal."
    )
    parser.add_argument(
        "--manifest-file",
        type=Path,
        required=True,
        help="The analysis manifest written by the portal (or by `yousleep-manifest` "
        "for a hand run).",
    )
    return parser.parse_args()


def create_event(label: str, start_ms: int, end_ms: int, channels: list[str]) -> Event:
    """
    Returns an Event with the given label, start and end times.

    `Event` is the platform contract (yousleep_common). Building real Event
    objects validates labels and times here, in the container, instead of at
    upload -- and `save_event_blocks` below encodes them into the block
    document, the one output format the platform accepts.
    """
    return Event(
        start_time_ms=start_ms,  # Start time of the event in milliseconds
        end_time_ms=end_ms,  # End time of the event in milliseconds
        label=label,  # Valid EDF+ label (e.g., 'Sleep stage ?')
        channels=channels,  # Optional channel names. Empty == all channels.
        # probability=None,  # If probabilistic, a float in [0, 1].
        # value=None,        # If valued, a float.
    )


def main():
    """
    The main analysis function which does roughly the following:
    1. Read the manifest.
    2. Load the EDF file it names.
    3. Write 'Sleep stage ?' events of length equal to the staging window length
       to the output path it names.
    """
    args = parse_args()
    manifest = load_manifest(args.manifest_file)
    logger.info(
        "Running %s for analysis %s with parameters %s on %d core(s)",
        manifest.analysis.config_id,
        manifest.analysis.id,
        manifest.parameters,
        manifest.resources.cpus,
    )
    # Custom parameters arrive validated and typed, with the configuration's
    # default filled in by the portal; the fallback here is for hand runs.
    window_ms = int(manifest.parameters.get("staging-window-length-ms", 30000))

    # Read the EDF file the manifest names. Channels are loaded by index and
    # attributed by the name the user gave them.
    recording = manifest.inputs.recording
    logger.info("Reading EDF file %s...", recording.path)
    edf_file = mne.io.read_raw_edf(recording.path, preload=False)
    sampling_rate = edf_file.info["sfreq"]
    channel_names = [channel.name for channel in recording.channels]

    # Compute how many staging windows the recording holds
    n_samples = edf_file.n_times
    length_ms = int(n_samples / sampling_rate * 1000)
    n_windows = math.ceil(length_ms / window_ms)
    logger.info("Number of staging windows: %d", n_windows)
    logger.info("Length of recording: %d ms", length_ms)

    # Create events
    logger.info("Creating events")
    events = []
    for epoch_index in range(n_windows):
        start_ms = epoch_index * window_ms
        end_ms = min(start_ms + window_ms, length_ms)
        events.append(create_event("Sleep stage ?", start_ms, end_ms, channel_names))

    # Write the events output document (block-encoded on the way out).
    # save_event_blocks is suffix-aware: the portal names an output path ending
    # .json.gz, and the document is written gzip-compressed there -- the
    # artifact stored on S3 is byte-identical to this file.
    output_path = Path(manifest.outputs.events.path)
    logger.info("Saving %d events to %s", len(events), output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_event_blocks(output_path, events)


if __name__ == "__main__":
    main()
