# YASA sleep staging

The finished project of the tutorial
[Package YASA](https://docs.yousleep.ai/build/example-yasa/): YASA's automatic sleep
staging ([Vallat and Walker, 2021](https://doi.org/10.7554/eLife.70092);
[source](https://github.com/raphaelvallat/yasa), BSD-3-Clause) packaged as a youSleep
analysis. The tutorial explains every file and the reasoning behind it.

| File | Purpose |
|---|---|
| `analysis.py` | Reads the manifest, loads the selected channels, runs YASA's classifier and writes the events document |
| `yasa-staging.yaml` | The configuration: what the analysis is, who developed it, what it needs from a recording and what it produces |
| `Dockerfile`, `requirements.in`, `requirements.txt` | The image, with every dependency pinned |
| `Makefile` | `make verify`, `make record`, `make run RECORDING=night.edf`, `make check` |
| `conformance/expected-events.json.gz` | The recorded output, compared on every `make verify` |

```bash
make verify                                            # build the image and run the check
make run RECORDING=night.edf MANIFEST_ARGS="--age 40 --sex male"
```

The Makefile runs the tools with `uvx`; see the tutorial for installing uv, or for
running the tools without it. YASA is not part of this repository: the image installs
it from PyPI under its own licence.
