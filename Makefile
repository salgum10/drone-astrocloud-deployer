.PHONY: plugin release

VERSION ?= latest

plugin:
	@echo "Building Drone plugin (export VERSION=<version> if needed)"
	docker build . -t lowess/drone-astrocloud-deployer:$(VERSION)

	@echo "\nDrone plugin successfully built! You can now execute it with:\n"
	@sed -n '/docker run/,/drone-astrocloud-deployer/p' README.md

release:
	@echo "Pushing Drone plugin to the registry"
	docker push lowess/drone-astrocloud-deployer:$(VERSION)
