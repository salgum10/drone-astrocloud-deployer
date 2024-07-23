#!/usr/bin/env python

"""Astrocloud deployer plugin to release new Astro projects packaged as Docker containers."""

import json
import sys
import requests
from plugin import dronecli, logger


class AstrocloudDeployer:
    """
    AstrocloudDeployer
    """

    def __init__(
        self,
        astronomer_api_token: str,
        organization_id: str,
        deployment_id: str,
        release_tag: str,
    ):
        """Create an AstrocloudDeployer."""
        self._deployment_id = deployment_id
        self._organization_id = organization_id
        self._release_tag = release_tag
        self._oauth_token = astronomer_api_token
        self._deploy_id = None
        self._repository = None
        self._tag = None

    def __repr__(self):
        """Representation of an AstrocloudDeployer object."""
        return "<{} 'org_id': {}, 'deployment_id': {} 'release_tag': {}>".format(
            self.__class__.__name__,
            self._organization_id,
            self._deployment_id,
            self._release_tag,
        )

    def initialize_deploy(self):
        """Initialize the deploy process and get the deploy ID, repository, and tag."""
        try:
            headers = {
                "Authorization": f"Bearer {self._oauth_token}",
                "Content-Type": "application/json",
                "X-Astro-Client-Identifier": "script"
            }
            data = {
                "type": "IMAGE_AND_DAG"
            }
            response = requests.post(
                f"https://api.astronomer.io/platform/v1beta1/organizations/{self._organization_id}/deployments/{self._deployment_id}/deploys",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            deploy_info = response.json()
            logger.debug(f"Deploy info: {json.dumps(deploy_info, indent=2)}")

            self._deploy_id = deploy_info.get('id')
            self._repository = deploy_info.get('imageRepository')
            self._tag = deploy_info.get('imageTag')

            if not self._deploy_id or not self._repository or not self._tag:
                logger.error(f"❌ Deploy initialization failed: {deploy_info}")
                raise ValueError("Deploy initialization failed")

            logger.info(f"Initialized deploy process: deploy_id={self._deploy_id}, repository={self._repository}, tag={self._tag}")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error during deploy initialization: {e}")
            raise

    def astro_deploy(self):
        """Runs the Astro deploy command with Docker image."""
        try:
            headers = {
                "Authorization": f"Bearer {self._oauth_token}",
                "Content-Type": "application/json",
                "X-Astro-Client-Identifier": "script"
            }
            data = {}
            response = requests.post(
                f"https://api.astronomer.io/platform/v1beta1/organizations/{self._organization_id}/deployments/{self._deployment_id}/deploys/{self._deploy_id}/finalize",
                headers=headers,
                json=data
            )
            response.raise_for_status()

            logger.info(f"🚀 Deploying Docker image to Astrocloud...")
            logger.info(f"🎉 Successfully updated Astrocloud deployment 🎉")

        except requests.exceptions.RequestException as e:
            logger.error(
                f"❌ Error occurred while deploying docker image to Astrocloud: {e}"
            )
            raise

    def run(self, dry_run: bool = False):
        """Main plugin logic."""
        self.initialize_deploy()
        if not dry_run:
            self.astro_deploy()

def main():
    """The main entrypoint for the plugin."""

    try:
        dry_run = dronecli.get("PLUGIN_DRY_RUN", False)
        organization_id = dronecli.get("PLUGIN_ORGANIZATION_ID")
        deployment_id = dronecli.get("PLUGIN_DEPLOYMENT_ID")
        release_tag = dronecli.get("PLUGIN_RELEASE_TAG")
        astronomer_api_token = dronecli.get("PLUGIN_ASTRONOMER_API_TOKEN")

        plugin = AstrocloudDeployer(
            organization_id=organization_id,
            deployment_id=deployment_id,
            release_tag=release_tag,
            astronomer_api_token=astronomer_api_token,
        )

        if dry_run:
            logger.warning("🚨 Dry run enabled, skipping deployment to Astrocloud!")

        logger.info("The drone plugin has been initialized with: {}".format(plugin))

        plugin.run(dry_run=dry_run)

    except Exception as e:
        logger.error("Error while executing the plugin: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
