# Packaging an analysis for the youSleep Portal

Two worked examples of an analysis the portal can run, and everything you need
to know to write your own. Copy one, replace the part that does the analysis,
and the rest stands.

| Directory | Shows |
|---|---|
| `example-sleep-staging-analysis/` | The common case: read a recording, produce one event per epoch |
| `example-downstream-analysis/` | An analysis that takes another analysis's events as its input |

Neither analyses anything. The staging one scores every epoch `Sleep stage ?`.
What they demonstrate is the interface, so that swapping in your own scoring
leaves everything else working.

## How the portal runs an analysis

An analysis is a container image plus a configuration file. When a user runs
it on a recording, the portal:

1. fetches the recording, and any upstream events the configuration asks for,
   into a directory the container will see;
2. writes a **manifest**, a JSON document describing this run;
3. starts the container with one argument, the manifest's path;
4. collects the events document the container wrote, stores it, and presents
   it in the viewer and the reports.

The container runs confined: **no network**, a read-only root filesystem, no
capabilities, an unprivileged user, and a CPU and memory allowance from the
configuration. It holds no credential and never talks to the portal. Everything
it needs arrives as files, and everything it produces is a file it writes where
the manifest says. If your analysis phones home for weights, a licence check or
anything else, it will work on your machine and fail on the platform.

## The contract

The portal runs your container as:

```
<entrypoint> --manifest-file <path>
```

Nothing else: no other arguments, no environment variables you should rely on.
The path is wherever the portal put the manifest; your code opens it and does
not reason about where it is.

**What the manifest gives you**

| Field | What it is |
|---|---|
| `inputs.recording.path` | The recording file, on disk before you start |
| `inputs.recording.channels[]` | The channels selected for this run: `index` (position in the file), `source_name` (the header label at that position), `name` (what the user calls it), `type`, `unit`, `sample_rate` |
| `inputs.events.path` | An upstream events document, when the configuration declares an events input; absent otherwise |
| `inputs.metadata` | Subject and study context (age, sex, lights off and on), when the configuration declares a metadata input |
| `parameters` | The configuration's parameters by `key`, already validated and typed. Read them; do not parse them |
| `resources` | The cores and memory this run has. Size your thread pool from `cpus` |
| `outputs.events.path` | Where to write the result |
| `analysis.id`, `analysis.config_id` | Which run and which configuration this is, for logs and provenance |

**What you must produce**

One events document at `outputs.events.path`. Each event has a start and an
end in milliseconds from the start of the recording, a label from the EDF+
vocabulary, and the channels it applies to:

```json
{
  "start_time_ms": 0,
  "end_time_ms": 30000,
  "label": "Sleep stage W",
  "channels": ["EEG Fpz-Cz"]
}
```

`channels` names the channels as the user knows them, the manifest's `name`,
and an empty list means the whole recording. Two optional fields exist,
`probability` in `[0, 1]` and `value`, each usable only when the configuration
declares that the analysis produces them. The full model is
[`yousleep_common.models.events.Event`](https://pypi.org/project/yousleep-common/).

Exit with status `0` after writing, and non-zero on any failure. A container
that exits `0` without writing the document has failed silently, which is
worse.

Any language will do. A manifest is JSON and an events document is JSON. The
helpers below are Python because the examples are; nothing requires them.

## Three helpers, each optional

[`yousleep-common`](https://pypi.org/project/yousleep-common/) on PyPI carries
the platform's models and three functions that do the parts every Python
analysis would otherwise write identically:

```python
import mne
from yousleep_common.utils.manifest import load_manifest
from yousleep_common.utils.analysis import select_channels
from yousleep_common.utils.event_blocks import save_event_blocks

manifest = load_manifest(path)                                        # validated, typed
raw = mne.io.read_raw_edf(manifest.inputs.recording.path)             # or any EDF reader
selected = select_channels(manifest, header_labels=raw.ch_names)      # refuses the wrong file
raw.pick([channel.index for channel in selected])                     # select by index
save_event_blocks(manifest.outputs.events.path, events)               # the encoding the portal reads
```

The manifest already names the channels to read, by index. `select_channels`
returns them, and the labels you pass are not used to choose anything: they
are the file's header labels in file order (`raw.ch_names` in MNE,
`getSignalLabels()` in pyedflib), and the helper checks that the label at
each named index is the `source_name` the manifest recorded, raising before
any signal is read if it is not. That is the whole point of the argument: a
file that is not the one the manifest describes fails loudly instead of
being analysed as if it were.

Take any of them or none. If your environment cannot accept the package's
dependency floors, read the JSON yourself; that is a complete path, not a
fallback.

**The one rule worth stating on its own.** Channels are selected **by index,
never by label**. A recording may repeat a label, and a user may rename a
channel, so an analysis that matches on a name can read a different signal
than the one the portal selected, and it will do so silently, producing
plausible results for the wrong data. `select_channels` checks that the label
at each index is the one the manifest names and refuses the file if not,
before any signal is read. Both examples use it; if you write your own, do the
same check.

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

The events document lands at `output-events.json.gz` in the working
directory. `--network none` is there because the portal runs it that way.

To run the script without Docker, the manifest's paths have to be the host's:
add `--recording-path night.edf --output-path events.json.gz` when writing
it, install `"mne>=1.9,<2"` beside the package, and run
`python example-sleep-staging-analysis/example-sleep-staging-analysis.py --manifest-file manifest.json`.

The downstream example additionally needs `--events-path`, pointing at an
events document from an earlier run.

## The configuration file

Each example directory holds the YAML that registers it with the portal. It
says what the analysis is, who wrote it, what it needs and what it produces,
and it is read by the catalogue, the submission form, the dispatcher and the
attribution page. The annotated files are the reference; the fields an author
writes are:

| Block | What you say |
|---|---|
| `identification` | Its name |
| `purpose` | What it does, which analysis types it belongs to, tags |
| `provenance` | Who developed it, and for software published elsewhere, where and under what licence. Shown to users; it has to be true |
| `evidence` | What it cites, each marked as the developer's own or independent. May be empty |
| `docker` | The image and tag |
| `resources` | Cores, and a base memory figure |
| `licence` | The licence class it is offered under |
| `inputs` | The recording it needs, by channel types or exact channels; events or metadata if it consumes them |
| `outputs` | The event labels it produces |
| `parameters` | What a user can set, typed, with defaults and choices. Omit if none |

Everything else is decided at registration and does not belong in the file:
scheduling priority, pricing, the image digest, GPU placement, and the memory
terms that scale with recording length, which the platform team measures.

## Before you submit

`yousleep-verify` runs an image the way the portal does and checks what it
wrote. Each example carries the document its image produced on the check's
synthetic recording, so a rebuild is compared against it:

```bash
pip install yousleep-common
yousleep-verify --image ghcr.io/yousleep-ai/yousleep/example-sleep-staging-analysis:1.2.0 \
    --config example-sleep-staging-analysis/example-sleep-staging-analysis.yaml \
    --expected example-sleep-staging-analysis/conformance/expected-events.json.gz
```

For your own analysis, run it with `--record` once to write the expected
document, commit it beside the configuration, and run it in CI on every
build. The full list of checks, and what they do not cover, is in the
package's documentation under *Checking an image*.

## From a script to the portal

Today, registration is done with the platform team. You provide the image,
either as a reference we can pull or as a `docker save` archive, and the
configuration file. We run the image against a real manifest under the same
confinement the platform uses, pin its digest, set the fields that are ours to
set, and register it. Your image is then copied into a registry the platform
controls, because a past analysis has to stay re-runnable and that cannot
depend on a registry we do not control.

A self-service path, with the same checks run by a tool you can use yourself
before submitting, is being designed. Until it exists, get in touch through
the portal's contact form and choose *Integrate an algorithm*.

## Licence

Apache 2.0, see [LICENSE](./LICENSE). These are examples to copy and adapt: an
analysis you build from one is yours, and nothing here asks you to license your
own work under these terms.
