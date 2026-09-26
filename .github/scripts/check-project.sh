#!/usr/bin/env bash
# Builds one project's image for linux/amd64, the platform's architecture, and
# runs the conformance check against the project's recorded output. Both
# workflows run it, so a published image has passed the same check as a pull
# request.
#
# Usage: check-project.sh <project directory> <image reference>
set -euo pipefail

project="$1"
ref="$2"

configs=("$project"/*.yaml)
if [ "${#configs[@]}" -ne 1 ] || [ ! -f "${configs[0]}" ]; then
  echo "::error::$project must hold exactly one configuration file"
  exit 1
fi
expected="$project/conformance/expected-events.json.gz"
if [ ! -f "$expected" ]; then
  echo "::error::$project has no recorded output at $expected"
  exit 1
fi

docker build --platform linux/amd64 \
  --label "org.opencontainers.image.revision=${GITHUB_SHA:-unknown}" \
  --tag "$ref" "$project"
yousleep-verify --image "$ref" --config "${configs[0]}" --expected "$expected"
