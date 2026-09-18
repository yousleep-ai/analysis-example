# youSleep Portal Minimal Analysis Example

A minimal youSleep Portal analysis example showing how to package a an analysis script and interface with the youSleep Portal.

At minimum, to implement an analysis into youSleep Portal, a repository (like this one) must contain the following 3 files:

1. An **analysis configuration** `YAML` file, see [example.yaml](./example.yaml). The analysis configuration defines the interface between youSleep Portal and this analysis script. At a high level, an analysis maps one or more of the following: Recording EDF file(s), an event file (JSON) and a metadata file (JSON) to an output events file (JSON). The output events file contains a list of [Events](#events).

2. The analysis script or package that performs the actual analysis, see e.g., [example-sleep-staging-analysis.py](./example-sleep-staging-analysis/example-sleep-staging-analysis.py). Any language and packaging can be used. The portal invokes the container with **one argument**, `--manifest-file <path>`, and nothing else. The manifest is a JSON document (`yousleep_common.models.AnalysisManifest`) naming the recording and the output path as the container sees them, the channels selected for the run (by index, with their header label and display name), the custom parameters typed as the analysis configuration declared them, and the resources the run has. The script reads it, does its work, and writes the events document to the manifest's output path.

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

Where `start_time_ms` and `end_time_ms` are the start and end times of the event in milliseconds relative to the begining of the recording, `label` is an `EDF+` label (no other strings allowed) of the event, `channels` is a list of the channels that the event is associated with (can be empty to signify global/all channels event), `probability` is an optional field giving the probability in [0, 1] of the event, and `value` is an optional field giving value associated with the event.

## Example (stand-alone) usage

`yousleep-manifest` (installed with `yousleep-common`) writes a manifest from an
EDF header, so an analysis runs outside the portal in two commands:

```bash
pip install "yousleep-common>=24" mne==1.7.1
yousleep-manifest --recording ../usleep/tests/test_data/SC4761E0-PSG.edf \
    --recording-path ../usleep/tests/test_data/SC4761E0-PSG.edf \
    --output-path ./output-events.json.gz \
    --config-id example-sleep-staging-analysis-v1 \
    --channel "EEG Fpz-Cz" --param staging-window-length-ms=30000 \
    --cpus 1 --memory-mib 1000 > manifest.json
python example-sleep-staging-analysis/example-sleep-staging-analysis.py --manifest-file manifest.json
```

In Docker, mount the working directory at `/local` and let the paths default:

```bash
yousleep-manifest --recording night.edf --config-id example-sleep-staging-analysis-v1 > manifest.json
docker run --rm -v "$PWD:/local" ghcr.io/yousleep-ai/yousleep/example-sleep-staging-analysis:latest \
    --manifest-file /local/manifest.json
```

The downstream example additionally needs `--events-path` pointing at an
upstream events document. The exact manifest the portal gives each registered
analysis is committed in the platform repository as
`tests/contract/dispatch_manifest.json`; the analysis configuration YAMLs in
this repository are copies of the registered ones.
