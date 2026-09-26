# The standard targets of a youSleep analysis project.
#
#   make verify                 build the image and run the conformance check
#   make run RECORDING=x.edf    run the image by hand on a recording
#   make record                 record the expected output for regression runs
#   make check                  validate the configuration only

CONFIG    := yasa-staging.yaml
IMAGE     := ghcr.io/example/yasa-staging:dev
RECORDING ?= night.edf
EXPECTED  := conformance/expected-events.json.gz
VERIFY_ARGS ?=
# The channels make run gives the analysis. Empty, the default, selects them as
# the platform does; to choose, list header labels separated by commas:
#   make run RECORDING=x.edf CHANNELS="EEG Fpz-Cz,EOG horizontal"
CHANNELS ?=
# Further yousleep-manifest flags, the subject values for example:
#   make run RECORDING=x.edf MANIFEST_ARGS="--age 40 --sex female"
MANIFEST_ARGS ?=
comma := ,
CHANNEL_FLAGS = $(if $(strip $(CHANNELS)),--channel '$(subst $(comma),' --channel ',$(CHANNELS))')

# How the yousleep tools run. Written by yousleep-init from how it was itself
# run (uvx). When that no longer applies, in a clone on another
# machine for example, the fallbacks look for the yousleep-verify command on
# the PATH (a deliberate install, pipx or uv tool), then for python3 or python
# with the package, then uvx pinned to the version requirements.txt pins. The
# tools target says which one runs and at which version, and notes when that
# differs from the pin. Override with:  make VERIFY="..." MANIFEST="..." verify
# The platform runs images on linux/amd64. Building for it here, even on an
# arm64 machine, keeps the recorded document comparable with the platform's
# run: floating-point results differ between architectures.
PLATFORM ?= linux/amd64
VERIFY   ?= uvx --from yousleep-common==33.4.0 yousleep-verify
MANIFEST ?= uvx --from yousleep-common==33.4.0 yousleep-manifest
PIN      := $(shell sed -n 's/^yousleep-common==\([^ ]*\).*/\1/p' requirements.txt)
ifeq ($(shell $(VERIFY) --help >/dev/null 2>&1 && echo ok),)
  PYTHON := $(shell for p in python3 python; do "$$p" -c "import yousleep_common" >/dev/null 2>&1 && { echo "$$p"; break; }; done)
  ifneq ($(shell command -v yousleep-verify 2>/dev/null),)
    VERIFY   := yousleep-verify
    MANIFEST := yousleep-manifest
  else ifneq ($(PYTHON),)
    VERIFY   := $(PYTHON) -m yousleep_common.cli.verify
    MANIFEST := $(PYTHON) -m yousleep_common.cli.manifest
  else ifneq ($(shell command -v uvx 2>/dev/null),)
    VERIFY   := uvx --from yousleep-common$(if $(PIN),==$(PIN),) yousleep-verify
    MANIFEST := uvx --from yousleep-common$(if $(PIN),==$(PIN),) yousleep-manifest
  else
    VERIFY   :=
    MANIFEST :=
  endif
endif

.PHONY: tools build manifest run verify record check clean

tools:
	@test -n "$(VERIFY)" || { \
	  echo "No way to run the yousleep tools was found: the recorded command does not run,"; \
	  echo "no yousleep-verify on the PATH, no python3 or python has yousleep-common, no uvx."; \
	  echo "  pip install yousleep-common    or    make VERIFY=\"python -m yousleep_common.cli.verify\" $(MAKECMDGOALS)"; \
	  exit 1; }
	@v=$$($(VERIFY) --version 2>/dev/null | sed 's/.* //'); \
	echo "yousleep tools: $(VERIFY)  (version $${v:-unknown})"; \
	if [ -n "$(PIN)" ] && [ -n "$$v" ] && [ "$$v" != "$(PIN)" ]; then \
	  echo "note: requirements.txt pins yousleep-common==$(PIN) but the tools run $$v;"; \
	  echo "      for the same version:  make VERIFY=\"uvx --from yousleep-common==$(PIN) yousleep-verify\" MANIFEST=\"uvx --from yousleep-common==$(PIN) yousleep-manifest\" $(MAKECMDGOALS)"; \
	fi

build:  ## Build the image for the platform's architecture (override PLATFORM to build for this machine)
	docker build --platform $(PLATFORM) -t $(IMAGE) .

manifest: tools  ## Write the manifest the platform would write for RECORDING
	$(MANIFEST) --recording $(RECORDING) --config $(CONFIG) $(CHANNEL_FLAGS) $(MANIFEST_ARGS) > manifest.json

run: build manifest  ## Run the image by hand; the events document lands in ./output-events.json.gz
	docker run --rm --network none -v "$(CURDIR):/local" $(IMAGE) --manifest-file /local/manifest.json

verify: tools build  ## The conformance check, against the recorded output when there is one
	$(VERIFY) --image $(IMAGE) --config $(CONFIG) \
		$(if $(wildcard $(EXPECTED)),--expected $(EXPECTED),) $(VERIFY_ARGS)

record: tools build  ## Record this build's output as the expected document
	$(VERIFY) --image $(IMAGE) --config $(CONFIG) --expected $(EXPECTED) --record

check: tools  ## Validate the configuration without running anything
	$(VERIFY) --image $(IMAGE) --config $(CONFIG) --config-only

clean:
	rm -f manifest.json output-events.json.gz
