# analysis-example

A minimal youSleep Portal analysis example showing how to package a an analysis script and interface with the youSleep Portal.

At minimum, to implement an analysis into youSleep Portal, a repository (like this one) must contain the following 3 files:

1. An **analysis configuration** `YAML` file, see [example.yaml](./example.yaml). The analysis configuration defines the interface between youSleep Portal and this analysis script. At a high level, an analysis maps one or more of the following: Recording EDF file(s), an event file (JSON) and a metadata file (JSON) to an output events file (JSON). The output events file contains a list of [Events](#events).

2. The analysis script or package that performs the actual analysis, see e.g., [example-analysis.py](./example-analysis.py). Any language and packaging can be used. The analysis script must accept a set of mandatory input arguments (see `parameters.default` field in the analysis configuration). It can optionally define any number of custom input parameters which must be specified by the user of the script via the youSleep Portal UI. The analysis script must output a JSON file containing a list of `events` (see above) to be saved at a path passed with the `--output-file` argument.

3. A [Dockerfile](./Dockerfile) that wraps the analysis script and its dependencies into a Docker container.

## Events
All events are represented as a list of dictionaries, where each dictionary represents an event. Each event dictionary must contain the following fields:

```json
{
  "start_time_ms": 0,
  "end_time_ms": 30000,
  "label": "Sleep stage W",
  "channels": ["EEG Fpz-Cz"],
  //"probability": 0.5,  // optional, for 'probabilistic' events only, see analysis config
  //"value": 5.0,        // optional, for 'valued' events only, see analysis config
}
```

Where `start_time_ms` and `end_time_ms` are the start and end times of the event in milliseconds relative to the begining of the recording, `label` is an `EDF+` label (no other strings allowed) of the event, `channels` is a list of the channels that the event is associated with (can be empty to signify global/all channels event), `probability` is an optional probability in [0, 1] of the event, and `value` is an optional the value associated with the event.

## Example (stand-alone) usage

```bash
python example-analysis.py \
    --input-file ../yousleep-analyses/tests/test_data/SC4761E0-PSG-1.edf \
    --output-file ./output-events.json \
    --channel-names Fpz-Cz \
    --channel-types EEG \
    --channel-units uV \
    --cpus 1 \
    --memory-mib 1000 \
    --staging-window-length-ms 30000
```
