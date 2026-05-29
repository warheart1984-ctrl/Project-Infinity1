.PHONY: run worker test governance-check rootfs iso-tree rootfs-forge iso-tree-forge forge-installer forge-shippable-gate forge-platform-gate forge-dashboard forge-nightly-evolution forge-nightly-build installer-smoke installer-integration sign-artifacts verify-artifacts ugr-cloud-gate ugr-ingestion-gate ugr-platform-gate ugr-graph-index-gate ugr-embryo-gate ugr-causal-graph-gate ugr-llm-provider-gate ugr-cogos-write-path-gate ugr-graph-backend-gate ugr-trust-bundle-gate ugr-operator-console-gate

FORGE_PROFILE ?= $(COGOS_FORGE_PROFILE)
FORGE_PROFILE_ARG := $(if $(strip $(FORGE_PROFILE)),--profile $(FORGE_PROFILE),)

run:
	uvicorn app.main:app --reload

worker:
	celery -A app.celery_app.celery worker --loglevel=info

test:
	pytest -q

governance-check:
	python3 .github/scripts/validate-governance-ledger.py

rootfs:
	sudo bash wolf-cog-os/scripts/build-rootfs.sh $(FORGE_PROFILE_ARG)

iso-tree:
	COGOS_BUILD_FROM_TREE=1 bash wolf-cog-os/scripts/build.sh $(FORGE_PROFILE_ARG) "$${ISO:-}"

rootfs-forge:
	sudo bash wolf-cog-os/scripts/build-rootfs.sh --profile "$${COGOS_FORGE_PROFILE:-forge-selfhosted}"

iso-tree-forge:
	COGOS_BUILD_FROM_TREE=1 bash wolf-cog-os/scripts/build.sh --profile "$${COGOS_FORGE_PROFILE:-forge-selfhosted}" "$${ISO:-}"

forge-installer:
	bash wolf-cog-os/scripts/build-forge-installer.sh "$${ISO:-}"

forge-shippable-gate:
	python3 .github/scripts/check-forge-shippable-gate.py --mode fail

forge-platform-gate:
	python3 .github/scripts/check-forge-platform-gate.py --mode fail

forge-dashboard:
	python3 wolf-cog-os/scripts/forge-platform-dashboard.py $(FORGE_DASHBOARD_ARGS)

forge-nightly-evolution:
	bash wolf-cog-os/scripts/test/forge-nightly-evolution.sh --dry-run

forge-nightly-build:
	bash wolf-cog-os/scripts/test/forge-nightly-evolution.sh --build

forge-run-pipeline:
	bash wolf-cog-os/scripts/run-forge-pipeline.sh $(PIPELINE)

installer-smoke:
	bash wolf-cog-os/scripts/cogos-installer.sh --smoke $(INSTALLER_ARGS)

installer-integration:
	python3 wolf-cog-os/scripts/test/installer-matrix.py

sign-artifacts:
	bash .github/scripts/sign-artifacts.sh "$(ARTIFACT_DIR)"

verify-artifacts:
	bash .github/scripts/verify-artifacts.sh "$(ARTIFACT_DIR)"

ugr-cloud-gate:
	python3 wolf-cog-os/scripts/validate-ugr-cloud-manifest.py --mode fail
	pytest tests/test_ugr_cloud.py -q

ugr-ingestion-gate:
	python3 wolf-cog-os/scripts/validate-ugr-ingestion-manifest.py --mode fail
	pytest tests/test_ugr_ingestion.py -q

ugr-platform-gate:
	python3 wolf-cog-os/scripts/validate-ugr-platform-manifest.py --mode fail
	pytest tests/test_ugr_platform.py -q

ugr-graph-index-gate:
	python3 wolf-cog-os/scripts/validate-ugr-graph-index-manifest.py --mode fail
	pytest tests/test_ugr_graph_index.py -q

ugr-embryo-gate:
	python3 wolf-cog-os/scripts/validate-ugr-embryo-manifest.py --mode fail
	pytest tests/test_ugr_embryo.py -q

ugr-causal-graph-gate:
	python3 wolf-cog-os/scripts/validate-ugr-causal-graph-manifest.py --mode fail
	pytest tests/test_ugr_causal_graph.py -q

ugr-llm-provider-gate:
	python3 wolf-cog-os/scripts/validate-ugr-llm-provider-manifest.py --mode fail
	pytest tests/test_ugr_governed_llm_executor.py tests/test_ugr_llm_lane.py -q

ugr-cogos-write-path-gate:
	python3 wolf-cog-os/scripts/validate-ugr-cogos-write-path-manifest.py --mode fail
	pytest tests/test_ugr_cogos_pattern_bridge.py tests/test_unified_pattern_ledger.py -q

ugr-graph-backend-gate:
	python3 wolf-cog-os/scripts/validate-ugr-graph-backend-manifest.py --mode fail
	pytest tests/test_ugr_graph_backend.py tests/test_ugr_graph_index.py -q

ugr-trust-bundle-gate:
	python3 wolf-cog-os/scripts/validate-ugr-trust-bundle-manifest.py --mode fail
	pytest tests/test_ugr_trust_bundle_organ.py -q
	python3 tools/proof/run_ugr_trust_bundle.py --mode fail

ugr-operator-console-gate:
	python3 wolf-cog-os/scripts/validate-ugr-operator-console-manifest.py --mode fail
	pytest tests/test_ugr_operator_console.py -q
