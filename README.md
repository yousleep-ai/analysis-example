# Packaging an analysis for the youSleep Portal

Two worked examples of an analysis container the portal can run, and the
contract they implement. Copy one and replace the part that does the analysis.

## The contract, in full

The portal runs your container with **one argument and nothing else**:

```
--manifest-file /local/manifest.json
```

The manifest is a JSON document naming the recording, the channels selected
for this run, the parameters your configuration declared, the resources the
run has, and the path to write the result to. Your container reads it, does
its work, and writes an events document where the manifest says.

That is the whole interface. There is no network, no callback, no API key and
no second argument. A container runs with networking disabled, a read-only
root filesystem, dropped capabilities and an unprivileged user, so everything
it needs must arrive as files and everything it produces must be written to
the output path.

Any language will do. The examples are Python because the helpers are, but a
manifest is JSON and an events document is JSON, so nothing here requires it.

## What is in this repository

| Directory | Shows |
|---|---|
| `example-sleep-staging-analysis/` | The common case: read a recording, produce one event per epoch |
| `example-downstream-analysis/` | An analysis that consumes another analysis's events as its input |

Each holds a script, a `Dockerfile`, its dependencies, and the analysis
configuration YAML that registers it with the portal.

Neither example analyses anything. The staging one scores every epoch
`Sleep stage ?`. What they demonstrate is the interface, so that replacing the
scoring loop with your own leaves everything else standing.

## The one rule most worth getting right

**Select channels by index, never by label.**

The manifest gives each selected channel an `index`, the position of the
signal in the EDF; a `source_name`, the label the file's header carries at
that position; and a `name`, what the user calls that channel in the portal,
which is what belongs in your output.

An EDF may repeat a label, and a user may rename a channel. An analysis that
matches on a name can therefore read a different signal than the one the
portal selected, and it will do so silently, producing plausible results for
the wrong data. Both examples check that the label at the index is the one the
manifest expects and then take the index, which is the pattern to copy.

## Running one locally

`yousleep-manifest` ships with `yousleep-common` and writes a manifest from an
EDF header, so an analysis runs outside the portal without any of it:

```bash
pip install yousleep-common "mne>=1.9,<2"

yousleep-manifest --recording night.edf \
    --config-id example-sleep-staging-analysis-v1 \
    --channel "EEG Fpz-Cz" \
    --param staging-window-length-ms=30000 \
    --cpus 1 --memory-mib 1000 > manifest.json

python example-sleep-staging-analysis/example-sleep-staging-analysis.py \
    --manifest-file manifest.json
```

Use any EDF recording you have. `--channel` names the header labels to select,
and the generator resolves them to indices for you.

In Docker, mount the working directory at `/local` and let the paths default:

```bash
docker build -t my-analysis example-sleep-staging-analysis/
docker run --rm --network none -v "$PWD:/local" my-analysis \
    --manifest-file /local/manifest.json
```

Pass `--network none`, because the portal does, and an analysis that only
works with networking will fail there and not here.

The downstream example additionally needs `--events-path`, pointing at an
events document from an earlier run.

## The events document

An analysis writes a list of events. Each one is:

```json
{
  "start_time_ms": 0,
  "end_time_ms": 30000,
  "label": "Sleep stage W",
  "channels": ["EEG Fpz-Cz"]
}
```

`start_time_ms` and `end_time_ms` are relative to the start of the recording.
`label` must be a valid EDF+ label rather than an arbitrary string. `channels`
attributes the event, and an empty list means the whole recording. Two
optional fields exist: `probability`, a float in `[0, 1]`, and `value`, a
float, each usable only when the analysis configuration declares that the
analysis produces them.

`save_event_blocks` writes this in the encoding the portal accepts, and is
aware of the output path's suffix, so a path ending `.json.gz` is written
gzip-compressed. If you are not using Python, write the same structure.

## Licence

Apache 2.0, see [LICENSE](./LICENSE). These are examples to copy and adapt: an
analysis you build from one is yours, and nothing here asks you to license
your own work under these terms.
