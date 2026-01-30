.PHONY: help docker-build docker-push docker-test

VERSION ?= latest
IMAGE_BASE := ghcr.io/yousleep-ai/yousleep/example-sleep-staging-analysis

help: ## Show this help message
	@echo "Example Sleep Staging Analysis - Docker Build Commands"
	@echo ""
	@echo "Multi-arch support: amd64 + arm64"
	@echo ""
	@echo "Usage: make <target> VERSION=x.y.z"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

docker-build: ## Build and push multi-arch image (amd64 + arm64)
	@echo "Building and pushing for amd64 and arm64..."
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-t $(IMAGE_BASE):$(VERSION) \
		$(if $(filter-out latest,$(VERSION)),-t $(IMAGE_BASE):latest,) \
		--push \
		.
	@echo "✅ Pushed: $(IMAGE_BASE):$(VERSION)"

docker-push: docker-build ## Alias for docker-build

docker-test: ## Build test image for current platform
	docker buildx build \
		-t example-sleep-staging-analysis:test \
		--load \
		.
	@echo "✅ Test image built. Run with:"
	@echo "   docker run example-sleep-staging-analysis:test --help"
