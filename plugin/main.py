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

        # Stores the oauth token to make subsequent requests
        self._astro_api = "https://api.astronomer.io/hub/v1"
        self._oauth_token = astronomer_api_token

    def __repr__(self):
        """Representation of an AstrocloudDeployer object."""
        return "<{} 'org_id': {}, 'deployment_id': {} 'release_tag': {}>".format(
            self.__class__.__name__,
            self._organization_id,
            self._deployment_id,
            self._release_tag,
        )

    def get_docker_image(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._oauth_token}",
        }

        graphql_query = """
            mutation imageCreate($input: ImageCreateInput!) {
                imageCreate(input: $input) {
                    id
                    tag
                    repository
                    digest
                    env
                    labels
                    deploymentId
                }
            }
        """

        payload = {
            "query": graphql_query,
            "variables": {
                "input": {
                    "deploymentId": self._deployment_id,
                    "tag": self._release_tag,
                }
            },
        }
        response = None
        try:
            response = requests.post(
                self._astro_api,
                headers=headers,
                data=json.dumps(payload),
            )
            response.raise_for_status()

            logger.info(f"🔎 Retrieving Docker image ID from Astrocloud...")
            image = response.json()["data"]["imageCreate"]
            logger.info(
                f"""🐳 Astrocloud Docker image spec are:

                    #️⃣ ID:          {image['id']}
                    🏷️ Tag:         {image['tag']}
                    🏠 Repository: {image['repository']}
            """
            )
            return image["id"]
        except:
            logger.error(f"❌ Error while retrieving docker image: {response.json()}")

    def deploy_image(self, image_id: str):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._oauth_token}",
        }

        graphql_query = """
            mutation imageDeploy($input: ImageDeployInput!) {
                imageDeploy(input: $input) {
                    id
                    deploymentId
                    digest
                    env
                    labels
                    name
                    tag
                    repository
                }
            }
        """

        payload = {
            "query": graphql_query,
            "variables": {
                "input": {
                    "id": image_id,
                    "tag": self._release_tag,
                    "repository": f"images.astronomer.cloud/{self._organization_id}/{self._deployment_id}",
                }
            },
        }
        response = None
        try:
            response = requests.post(
                self._astro_api,
                headers=headers,
                data=json.dumps(payload),
            )
            response.raise_for_status()

            logger.info(f"🚀 Deploying Docker image ID '{image_id}' to Astrocloud...")
            response.json()
            logger.info(f"🎉 Successfully updated Astrocloud deployment 🎉")
        except:
            logger.error(
                f"❌ Error occured while deploying docker image to Astrocloud: {response.json()}"
            )

    def run(self, dry_run: bool = False):
        """Main plugin logic."""
        image_id = self.get_docker_image()
        if not dry_run:
           self.deploy_image(image_id)

def main():
    """The main entrypoint for the plugin."""

    try:
        dry_run = dronecli.get("PLUGIN_DRY_RUN", False)
        organization_id = dronecli.get("PLUGIN_ORGANIZATION_ID")
        deployment_id = dronecli.get("PLUGIN_DEPLOYMENT_ID")
        release_tag = dronecli.get("PLUGIN_RELEASE_TAG")
        astronomer_api_token = dronecli.get("PLUGIN_ASTRO_API_TOKEN")

        plugin = AstrocloudDeployer(
            organization_id=organization_id,
            deployment_id=deployment_id,
            release_tag=release_tag,
            astronomer_api_token=astronomer_api_token
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
