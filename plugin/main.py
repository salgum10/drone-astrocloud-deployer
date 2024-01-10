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
        astronomer_key_id: str,
        astronomer_key_secret: str,
        organization_id: str,
        deployment_id: str,
        release_tag: str,
    ):
        """Create an AstrocloudDeployer."""
        self._astronomer_key_id = astronomer_key_id
        self._astronomer_key_secret = astronomer_key_secret
        self._deployment_id = deployment_id
        self._organization_id = organization_id
        self._release_tag = release_tag

        # Stores the oauth token to make subsequent requests
        self._astro_api = "https://api.astronomer.io/hub/v1"
        self._oauth_token = None

    def __repr__(self):
        """Representation of an AstrocloudDeployer object."""
        return "<{} 'org_id': {}, 'deployment_id': {} 'release_tag': {}>".format(
            self.__class__.__name__,
            self._organization_id,
            self._deployment_id,
            self._release_tag,
        )

    def _fetch_oauth_token(self):
        headers = {"Content-Type": "application/json"}

        payload = {
            "client_id": self._astronomer_key_id,
            "client_secret": self._astronomer_key_secret,
            "audience": "astronomer-ee",
            "grant_type": "client_credentials",
        }

        response = None

        try:
            response = requests.post(
                "https://auth.astronomer.io/oauth/token",
                headers=headers,
                data=json.dumps(payload),
            )
            response.raise_for_status()
            self._oauth_token = response.json()["access_token"]
            logger.info(f"🔑 Successfully retrieved Astronomer OAuth token!")
        except:
            logger.error(f"❌ Error while fetching oauth token: {response.json()}")

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
        """
        Deploy the Docker image to Astrocloud using the updated GraphQL mutation.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._oauth_token}",
        }

        # New GraphQL payload for deployment
        payload = json.dumps({
            "query": """mutation DeployImage($input: DeployImageInput!) {
                deployImage(
                  input: $input
                ) {
                  id
                  deploymentId
                  digest
                  env
                  labels
                  name
                  tag
                  repository
                }
            }""",
            "variables": {
                "input": {
                    "deploymentId": self._deployment_id,
                    "imageId": image_id,
                    "tag": self._release_tag,
                    "repository": f"images.astronomer.cloud/{self._organization_id}/{self._deployment_id}"
                }
            }
        })

        response = None
        try:
            response = requests.post(
                "https://api.astronomer.io/hub/graphql",
                headers=headers,
                data=payload,
            )
            response.raise_for_status()

            logger.info(f"🚀 Deploying Docker image ID '{image_id}' to Astrocloud...")
            logger.info(f"🎉 Successfully updated Astrocloud deployment 🎉")
        except Exception as e:
            logger.error(
                f"❌ Error occurred while deploying docker image to Astrocloud: {str(e)}"
            )

    def run(self, dry_run: bool = False):
        """Main plugin logic."""
        self._fetch_oauth_token()
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
        astronomer_key_id = dronecli.get("PLUGIN_ASTRONOMER_KEY_ID")
        astronomer_key_secret = dronecli.get("PLUGIN_ASTRONOMER_KEY_SECRET")

        plugin = AstrocloudDeployer(
            organization_id=organization_id,
            deployment_id=deployment_id,
            release_tag=release_tag,
            astronomer_key_id=astronomer_key_id,
            astronomer_key_secret=astronomer_key_secret,
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