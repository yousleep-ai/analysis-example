# Packaging an analysis for the youSleep Portal

This repository holds three worked examples of an analysis the portal can run.
To write your own, copy one and replace the part that performs the analysis.
The [packaging guide](https://docs.yousleep.ai/components/common/analysis-authoring/)
specifies the contract the examples follow.

| Directory | Shows |
|---|---|
| `example-sleep-staging-analysis/` | The common case: read a recording, produce one event per epoch |
| `example-downstream-analysis/` | An analysis that takes another analysis's events as its input |
| `yasa-sleep-staging/` | A published algorithm, YASA, packaged in full: the finished project of the [Package YASA](https://docs.yousleep.ai/build/example-yasa/) tutorial |

The first two examples perform no analysis. They show the interface, so that
replacing their scoring leaves the rest of the project working:

- The staging example scores every epoch `Sleep stage ?`.
- The downstream example writes an `EEG arousal` wherever its input events are
  `Sleep stage ?`.

To start from an empty directory instead, run `yousleep-init`, which is
installed with `yousleep-common`. It writes a project in the same form that
passes the conformance check as generated, as
[Starting a project](https://docs.yousleep.ai/components/common/init/) describes.

## How the portal runs an analysis

An analysis is a container image plus a configuration file. When a user runs
it on a recording, the portal:

1. fetches the recording, and any upstream events the configuration asks for,
   into a directory the container will see;
2. writes a **manifest**, a JSON document describing this run;
3. starts the container with one argument, the manifest's path;
4. collects the events document the container wrote, stores it, and presents
   it in the viewer and the reports.

The container runs confined:

- no network access;
- a read-only root filesystem, with a writable `/tmp`;
- no capabilities and an unprivileged user;
- the cores and memory the configuration declares;
- a time limit. A run is expected to finish within one minute and is stopped
  after two, regardless of recording length. A configuration that needs more
  time requests it at registration, with the reason.

The container holds no credential and never calls the portal. Every input
arrives as a file, and every output is a file the container writes where the
manifest says. An analysis that fetches model weights, a licence check or
anything else over the network at run time works locally and fails on the
platform, so copy every file it needs into the image.

## The contract

The portal runs your container as:

```
<entrypoint> --manifest-file <path>
```

The portal passes no other argument, and the container should not rely on any
environment variable. The path is wherever the portal put the manifest; your
code opens it and does not reason about where it is.

**What the manifest gives you**

| Field | What it is |
|---|---|
| `inputs.recording.path` | The recording file, on disk before you start |
| `inputs.recording.channels[]` | The channels selected for this run: `index` (position in the file), `source_name` (the header label at that position), `name` (what the user calls it), `type`, `unit`, `sample_rate`, and `slot` when the configuration declares slots |
| `inputs.events.path` | An upstream events document, when the configuration declares an events input; absent otherwise |
| `inputs.metadata` | Subject and study context (age, sex and BMI; lights off and on), when the configuration declares a metadata input. Only the subject values it declares are filled, each null when the study does not record it |
| `parameters` | The configuration's parameters by `key`, already validated and typed. Read them; do not parse them |
| `resources` | The cores and memory this run has. Size your thread pool from `cpus` |
| `outputs.events.path` | Where to write the result |
| `analysis.id`, `analysis.config_id` | Which run and which configuration this is, for logs and provenance |

[Analysis manifest](https://docs.yousleep.ai/components/common/analysis-manifest/)
specifies every field.

**What you must produce**

One events document at `outputs.events.path`. The document lists the events
as blocks: a block is a run of consecutive events of equal duration that
share a set of channels, with one label per slot.

```json
{
  "format_version": 1,
  "blocks": [
    {
      "origin_ms": 0,
      "period_ms": 30000,
      "labels": ["Sleep stage W", "Sleep stage W", "Sleep stage N1"],
      "probability": null,
      "value": null,
      "channels": ["Fpz-Cz"]
    }
  ]
}
```

- Slot `i` spans `origin_ms + i × period_ms` to `origin_ms + (i + 1) × period_ms`,
  in milliseconds from the start of the recording.
- Labels come from the EDF+ vocabulary, and only from the labels the
  configuration declares under `outputs.events`.
- `channels` names the channels by the manifest's `name`. An empty list means
  the whole recording.
- `probability` and `value` are lists with one entry per slot, written only
  for outputs the configuration declares `probabilistic` or `valued`, and
  `null` otherwise.
- The output path ends in `.json.gz`, and the file is written gzip-compressed.

In Python, `save_event_blocks` writes this document from a list of `Event`
objects, as the examples do. The
[events document](https://docs.yousleep.ai/components/common/events-document/)
page specifies the format in full, with its JSON Schema.

Exit with status `0` after writing, and non-zero on any failure. A container
that exits `0` without writing the document has failed without signalling it.

An analysis can be written in any language. The manifest and the events
document are JSON, and each is specified by a JSON Schema. The helpers below
are written in Python, as the examples are, and using them is optional.

## Helpers for Python

[`yousleep-common`](https://pypi.org/project/yousleep-common/) on PyPI contains
the platform's models and four functions that cover the steps every Python
analysis would otherwise implement itself:

```python
import mne
from yousleep_common.utils.manifest import load_manifest
from yousleep_common.utils.analysis import select_channels
from yousleep_common.utils.event_blocks import save_event_blocks

manifest = load_manifest(path)                                            # validated, typed
raw = mne.io.read_raw_edf(manifest.inputs.recording.path, preload=False)  # the header only
selected = select_channels(manifest, header_labels=raw.ch_names)          # refuses the wrong file
raw.pick([channel.index for channel in selected])                         # select by index
raw.load_data()                                                           # the selected signals only
save_event_blocks(manifest.outputs.events.path, events)                   # the encoding the portal reads
```

| Helper | What it does |
|---|---|
| `load_manifest(path)` | Reads the manifest and validates it into a typed `AnalysisManifest` |
| `select_channels(manifest, header_labels=...)` | Returns the channels the manifest names, by index, each with its `name`, `type` and `slot`. The header labels passed in (`raw.ch_names` in MNE, `getSignalLabels()` in pyedflib) are compared with the manifest's `source_name` at each index. If they differ, the helper raises before any signal is read |
| `channel_for_slot(selected, "EOG-L")` | Looks up a slot's channel by slot label, so that adding a slot to the configuration does not shift the ones after it |
| `save_event_blocks(path, events)` | Encodes a list of `Event` as an events document and compresses it when the path ends in `.gz` |

An environment that cannot accept the package's dependency floors can read and
write the JSON directly. Both paths are supported.

**Channels are selected by index, never by label.** A recording may repeat a
label, and a user may rename a channel. An analysis that matches on a name can
read a different signal than the one the portal selected, and then produces
plausible results for the wrong data without raising an error.
`select_channels` checks that the label at each index is the one the manifest
names and rejects the file before any signal is read. Every example uses it.
An analysis that does not use the helper should perform the same check.

## Running an example locally

Use any EDF recording you have.

```bash
pip install yousleep-common

# A manifest for a hand run, from the configuration: its id, cores, projected
# memory and parameter defaults, as the portal would write them. --channel
# names header labels; the tool resolves them to indices and refuses a
# selection the portal would refuse. Paths default to /local/…, which is
# where the Docker run below mounts the working directory.
yousleep-manifest --recording night.edf \
    --config example-sleep-staging-analysis/example-sleep-staging-analysis.yaml \
    --channel "EEG Fpz-Cz" > manifest.json

docker build -t my-analysis example-sleep-staging-analysis/
docker run --rm --network none -v "$PWD:/local" my-analysis --manifest-file /local/manifest.json
```

The events document is written to `output-events.json.gz` in the working
directory. Pass `--network none` because the portal runs the container without
network access.

To run the script without Docker, the manifest's paths have to be the host's:
add `--recording-path night.edf --output-path events.json.gz` when writing
it, install `"mne>=1.9,<2"` beside the package, and run
`python example-sleep-staging-analysis/example-sleep-staging-analysis.py --manifest-file manifest.json`.

The downstream example additionally needs `--events-path`, pointing at an
events document from an earlier run.
[Running a container by hand](https://docs.yousleep.ai/components/common/analysis-manifest/#running-a-container-by-hand)
lists the other options of `yousleep-manifest`.

## The configuration file

Each example directory holds the YAML that registers it with the portal. It
says what the analysis is, who wrote it, what it needs and what it produces,
and it is read by the catalogue, the submission form, the dispatcher and the
attribution page. The annotated files explain each field, and the
[configuration reference](https://docs.yousleep.ai/components/common/analysis-authoring/#the-configuration-file)
specifies them. The fields an author writes are:

| Block | What you say |
|---|---|
| `identification` | Its name |
| `purpose` | What it does, which analysis types it belongs to, tags |
| `provenance` | Who developed it, and for software published elsewhere, where, under what licence and on what basis it may be offered (`data_rights`). Shown to users; it has to be true |
| `evidence` | What it cites, each marked as the developer's own or independent. Omit it if there is nothing to cite yet |
| `docker` | The image and tag |
| `resources` | Cores, and a base memory figure |
| `licence` | The licence class it is offered under |
| `inputs` | The recording it needs, by channel types or exact channels; events or metadata if it consumes them |
| `outputs` | The event labels it produces, each optionally `probabilistic`, `valued` or `instant` |
| `parameters` | What a user can set, typed, with defaults and choices. Omit if none |

Everything else is decided at registration and does not belong in the file:

- scheduling priority and pricing;
- the image digest and GPU placement;
- the memory terms that scale with recording length, which the platform team
  measures;
- to whom the analysis is offered.

## Checking the image

`yousleep-verify` runs an image the way the portal does and checks what it
wrote. Each example carries the document its image produced on the check's
synthetic recording, so a rebuild is compared against it:

```bash
pip install yousleep-common
docker build -t my-analysis example-sleep-staging-analysis/
yousleep-verify --image my-analysis \
    --config example-sleep-staging-analysis/example-sleep-staging-analysis.yaml \
    --expected example-sleep-staging-analysis/conformance/expected-events.json.gz
```

For your own analysis:

1. Run the check with `--record` once to write the expected document. Record
   it from a `linux/amd64` build, the platform's architecture, because a
   model's probabilities can differ between architectures.
2. Commit the document beside the configuration.
3. Run the check in CI on every build.

[Checking an image](https://docs.yousleep.ai/components/common/conformance/)
lists every check and what the check does not cover.

## Registering an analysis

Registration is currently done together with the platform team, as
[Registration](https://docs.yousleep.ai/build/registration/) describes:

1. Contact us through the portal's contact form and choose *Integrate an
   algorithm*.
2. Send the image, as a reference we can pull or as a `docker save` archive,
   and the configuration file.
3. We run `yousleep-verify` on it for the platform's architecture, pin its
   digest, measure the memory terms that scale with recording length, set the
   other fields that are ours to set, and register it.
4. The image is copied into a registry the platform controls, so that past
   analyses remain re-runnable.

The analysis is offered first to the organisation it is registered for. One
developed outside youSleep is offered to every user once its developer's
signed Analysis Declaration is on record; we send the form.

## Licence

Apache 2.0, see [LICENSE](./LICENSE). The examples are meant to be copied and
adapted. An analysis you build from one is yours, and you choose the licence
for your own work.
