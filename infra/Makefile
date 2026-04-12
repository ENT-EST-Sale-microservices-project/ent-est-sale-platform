# ==============================================================================
# ENT EST Salé — Infrastructure Makefile
# ==============================================================================
.DEFAULT_GOAL := help
SHELL         := /bin/bash

ENV_FILE      ?= .env
-include $(ENV_FILE)
export

BOOTSTRAP     := ./bootstrap/bootstrap-infra.sh
CLUSTER_NAME  ?= ent-est
KUBE_CONTEXT  ?=

.PHONY: help kind prod clean env-check

## help : Show this help message
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'

## env-check : Verify .env exists (copy from .env.example if not)
env-check:
	@if [[ ! -f .env ]]; then \
	  echo "ERROR: .env not found. Copy and edit .env.example:"; \
	  echo "  cp .env.example .env"; \
	  exit 1; \
	fi

## kind : Bootstrap a local Kind cluster (dev)
kind: env-check
	$(BOOTSTRAP) \
	  --mode kind \
	  --cluster-name $(CLUSTER_NAME) \
	  --kind-config ./cluster/kind-config.yaml

## prod : Bootstrap on an existing cluster (staging / prod)
## Usage: make prod KUBE_CONTEXT=prod-admin@prod-cluster
prod: env-check
	@[[ -n "$(KUBE_CONTEXT)" ]] || { echo "ERROR: KUBE_CONTEXT is required."; exit 1; }
	$(BOOTSTRAP) \
	  --mode existing \
	  --kube-context $(KUBE_CONTEXT)

## clean : Delete the local Kind cluster
clean:
	kind delete cluster --name $(CLUSTER_NAME)
