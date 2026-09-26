"""YASA sleep staging on the youSleep platform.

Reads the manifest the platform writes, loads only the channels it selected,
runs YASA's pre-trained LightGBM staging classifier and writes one event per
30-second epoch: the predicted stage with its probability, or every stage's
probability when the store-all-probabilities parameter is set.

YASA: Vallat R. and Walker M.P. (2021), eLife 10:e70092,
https://github.com/raphaelvallat/yasa (BSD-3-Clause).
"""

from argparse import ArgumentParser
from pathlib import Path

import mne
import yasa
from yousleep_common.models.events import Event
from yousleep_common.utils.analysis import select_channels
from yousleep_common.utils.event_blocks import save_event_blocks
from yousleep_common.utils.manifest import load_manifest

# The generation of YASA's trained classifiers this analysis runs. YASA picks the
# newest it ships by default, so a release adding one would change results.
CLASSIFIERS = "0.5.0"

# YASA's stage names -> the platform's label vocabulary.
STAGES = {
    "WAKE": "Sleep stage W",
    "N1": "Sleep stage N1",
    "N2": "Sleep stage N2",
    "N3": "Sleep stage N3",
    "REM": "Sleep stage R",
}


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--manifest-file", required=True)
    manifest = load_manifest(parser.parse_args().manifest_file)

    raw = mne.io.read_raw_edf(manifest.inputs.recording.path, preload=False, verbose="ERROR")
    selected = select_channels(manifest, header_labels=raw.ch_names)  # refuses the wrong file
    header = {}
    for channel in selected:  # at most one EEG, one EOG and one EMG
        header.setdefault(channel.type, raw.ch_names[channel.index])
    raw.pick([channel.index for channel in selected])
    raw.load_data()  # reads the selected channels only

    # YASA's classifiers with demographics need an age and a binary sex; any
    # other case (a value missing, "other", "unknown", an age YASA refuses)
    # runs the classifier without demographics.
    subject = manifest.inputs.metadata.subject if manifest.inputs.metadata else None
    metadata = None
    if subject and subject.age and 0 < subject.age < 120 and subject.sex in ("male", "female"):
        metadata = {"age": subject.age, "male": subject.sex == "male"}

    staging = yasa.SleepStaging(raw, eeg_name=header["EEG"], eog_name=header.get("EOG"),
                                emg_name=header.get("EMG"), metadata=metadata)
    # The file YASA's "auto" would choose for these inputs, at the named generation.
    model = "clf_eeg" + "".join(
        suffix
        for suffix, used in (("+eog", "EOG" in header), ("+emg", "EMG" in header),
                             ("+demo", metadata is not None))
        if used
    )
    classifier = Path(yasa.__file__).parent / "classifiers" / f"{model}_lgb_{CLASSIFIERS}.joblib"
    hypnogram = staging.predict(path_to_model=str(classifier))  # stages per epoch, with .proba

    # One event per epoch for the predicted stage, or one per stage when the
    # user asks for every stage's probability.
    store_all = bool(manifest.parameters.get("store-all-probabilities", False))
    channels = [channel.name for channel in selected]
    events = []
    for i, stage in enumerate(hypnogram.hypno):
        probabilities = hypnogram.proba.iloc[i]
        for label in probabilities.index if store_all else [stage]:
            events.append(
                Event(start_time_ms=i * 30_000, end_time_ms=(i + 1) * 30_000,
                      label=STAGES[label], probability=float(probabilities[label]),
                      channels=channels)
            )

    output = Path(manifest.outputs.events.path)
    output.parent.mkdir(parents=True, exist_ok=True)
    save_event_blocks(output, events, device={"software": "yasa", "version": yasa.__version__})


if __name__ == "__main__":
    main()
