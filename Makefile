# Docker variables
VERSION := latest
SLEEP_STAGING_CONTAINER_URL := ghcr.io/yousleep-ai/yousleep/example-sleep-staging-analysis:$(VERSION)
DOWNSTREAM_CONTAINER_URL := ghcr.io/yousleep-ai/yousleep/example-downstream-analysis:$(VERSION)

.PHONY: build-docker
build-docker: ## Build the Docker image
	@echo "🚀 Building Docker images"
	@cd example-sleep-staging-analysis && \
		echo "🚀 Building $(SLEEP_STAGING_CONTAINER_URL)" && \
		docker build --ssh=default -t $(SLEEP_STAGING_CONTAINER_URL) . && \
		echo "🚀 Building $(DOWNSTREAM_CONTAINER_URL)" && \
		cd ../example-downstream-analysis && \
		docker build --ssh=default -t $(DOWNSTREAM_CONTAINER_URL) .

.PHONY: publish-docker
publish-docker: ## Publish the Docker image
	@echo "📦 Publishing Docker image to GitHub Container Registry"
	@cd example-sleep-staging-analysis && \
		echo "📦 Pushing $(SLEEP_STAGING_CONTAINER_URL)" && \
		docker push $(SLEEP_STAGING_CONTAINER_URL) && \
		echo "📦 Pushing $(DOWNSTREAM_CONTAINER_URL)" && \
		cd ../example-downstream-analysis && \
		docker push $(DOWNSTREAM_CONTAINER_URL)

.PHONY: build-and-publish-docker
build-and-publish-docker: build-docker publish-docker ## Build and publish the Docker image

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help
