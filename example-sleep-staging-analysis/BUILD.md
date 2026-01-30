# Multi-Architecture Build Instructions

This Docker image supports both **arm64** (Apple Silicon) and **amd64** (Intel/AMD) architectures.

## Image Naming Convention

```
ghcr.io/yousleep-ai/yousleep/example-sleep-staging-analysis:VERSION
ghcr.io/yousleep-ai/yousleep/example-sleep-staging-analysis:latest
```

**Example**: `example-sleep-staging-analysis:1.0.0`

## Prerequisites

```bash
# Create buildx builder (one-time setup)
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap
```

## Quick Build (Make Commands)

```bash
# Build for both architectures
make docker-build VERSION=1.0.0

# Build and push
make docker-push VERSION=1.0.0
```

## Manual Build Commands

### Multi-Arch Build and Push

```bash
VERSION=1.0.0

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/yousleep-ai/yousleep/example-sleep-staging-analysis:${VERSION} \
  -t ghcr.io/yousleep-ai/yousleep/example-sleep-staging-analysis:latest \
  --push \
  .
```

### Build for Single Platform (Testing)

```bash
# amd64 only (Linux servers)
docker buildx build \
  --platform linux/amd64 \
  -t example-sleep-staging-analysis:test \
  --load \
  .

# arm64 only (Apple Silicon)
docker buildx build \
  --platform linux/arm64 \
  -t example-sleep-staging-analysis:test \
  --load \
  .
```

## Notes

- Simple Ubuntu-based image, fully multi-arch compatible
- No special hardware requirements
- Works on both Mac (arm64) and Linux servers (amd64)
