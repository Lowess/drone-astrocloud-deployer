#!/usr/bin/env python

"""Astrocloud deployer plugin to release new Astro projects packaged as Docker containers."""

import json
import sys

import requests
from plugin import dronecli, logger


class AstrocloudDeployerException(Exception):
    pass

class AstrocloudDeployer:
    """
    AstrocloudDeployer
    """
    ASTRO_DEPLOY_FILE = ".astronomer-deploy.json"

    def __init__(
        self,
        astronomer_api_token: str,
        organization_id: str,
        deployment_id: str,
        deploy_id: str = None,
    ):
        """Create an AstrocloudDeployer."""
        self._deployment_id = deployment_id
        self._organization_id = organization_id

        # Stores the oauth token to make subsequent requests
        self._astro_api = "https://api.astronomer.io/platform/v1beta1"
        self._oauth_token = astronomer_api_token

        self._deploy_id = deploy_id
        self._repository = None
        self._tag = None

    def __repr__(self):
        """Representation of an AstrocloudDeployer object."""
        return "<{} 'org_id': {}, 'deployment_id': {}>".format(
            self.__class__.__name__,
            self._organization_id,
            self._deployment_id,
        )

    def initiate_deploy(self, description):
        """Initiate a deploy process and to generate a deploy ID, repository, and tag."""
        try:
            headers = {
                "Authorization": f"Bearer {self._oauth_token}",
                "Content-Type": "application/json",
                "X-Astro-Client-Identifier": "script"
            }

            data = {
                "type": "IMAGE_AND_DAG",
                "description": description,
            }

            response = requests.post(
                f"{self._astro_api}/organizations/{self._organization_id}/deployments/{self._deployment_id}/deploys",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            deploy_info = response.json()

            logger.debug(f"Deploy info: {json.dumps(deploy_info, indent=2)}")

            # Write deployment response to file
            with open(AstrocloudDeployer.ASTRO_DEPLOY_FILE, "w") as f:
                f.write(json.dumps(deploy_info, indent=2))

            self._deploy_id = deploy_info.get('id')
            self._repository = deploy_info.get('imageRepository')
            self._tag = deploy_info.get('imageTag')

            logger.info(
                f"""
                📲 Initiated Astrocloud Deployment process:

                    #️⃣ Deploy ID:   {self._deploy_id}
                    🏷️ Tag:         {self._tag}
                    🏠 Repository:  {self._repository}
            """)

        except requests.exceptions.RequestException as e:
            raise AstrocloudDeployerException(f"❌ Error during deploy initialization")

    def read_deploy_info(self):
        """Get the deploy info from file."""
        try:
            if not self._deploy_id:
                with open(AstrocloudDeployer.ASTRO_DEPLOY_FILE, "r") as f:
                    deploy_info = json.load(f)

                self._deploy_id = deploy_info.get('id')
                self._repository = deploy_info.get('imageRepository')
                self._tag = deploy_info.get('imageTag')

                logger.info(
                    f"""
                    👀 Retrieved Astrocloud deploy info from {AstrocloudDeployer.ASTRO_DEPLOY_FILE}:
                        #️⃣ Deploy ID:   {self._deploy_id}
                        🏷️ Tag:         {self._tag}
                        🏠 Repository: {self._repository}
                """)
            else:
                logger.info(
                    f"""
                    👀 Retrieved Astrocloud deploy info from plugin:
                        #️⃣ Deploy ID:   {self._deploy_id}
                """)

        except FileNotFoundError as e:
            raise Exception(f"❌ Error while reading deploy info file")

    def finalize_deploy(self):
        """Finalize a deployment that was previously initiated."""
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
            logger.info(f"🚀 Successfully updated Astrocloud deployment 🎉")

        except requests.exceptions.RequestException as e:
            raise AstrocloudDeployerException(
                f"❌ Error occurred while deploying docker image to Astrocloud: {response.json()}"
            )

    def rollback_deploy(self):
        """Runs the Astro deploy command with Docker image."""
        try:
            headers = {
                "Authorization": f"Bearer {self._oauth_token}",
                "Content-Type": "application/json",
                "X-Astro-Client-Identifier": "script"
            }
            data = {}
            response = requests.post(
                f"https://api.astronomer.io/platform/v1beta1/organizations/{self._organization_id}/deployments/{self._deployment_id}/deploys/{self._deploy_id}/rollback",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            logger.info(f"🚀 Successfully updated Astrocloud deployment 🎉")

        except requests.exceptions.RequestException as e:
            raise AstrocloudDeployerException(
                f"❌ Error occurred while deploying docker image to Astrocloud: {response.json()}"
            )
    def run(self, action: str, description: str = None):
        """Main plugin logic."""

        if action == "initiate":
            self.initiate_deploy(description)
        elif action == "finalize":
            self.read_deploy_info()
            self.finalize_deploy()
        elif action == "rollback":
            self.read_deploy_info()
            self.rollback_deploy()
        else:
            raise AstrocloudDeployerException(f"❌ Invalid action: {action}. Action must be one of 'initiate', 'finalize', or 'rollback'.")

def main():
    """The main entrypoint for the plugin."""

    try:
        astronomer_api_token = dronecli.get("PLUGIN_ASTRONOMER_API_TOKEN")
        organization_id = dronecli.get("PLUGIN_ORGANIZATION_ID")
        deployment_id = dronecli.get("PLUGIN_DEPLOYMENT_ID")

        deploy_id = dronecli.get("PLUGIN_DEPLOY_ID", default="")
        action = dronecli.get("PLUGIN_ACTION")
        description = dronecli.get("PLUGIN_DESCRIPTION", default="Deployment initiated by Drone CI")

        plugin = AstrocloudDeployer(
            astronomer_api_token=astronomer_api_token,
            organization_id=organization_id,
            deployment_id=deployment_id,
            deploy_id=deploy_id,
        )

        logger.info("The drone plugin has been initialized with: {}".format(plugin))

        plugin.run(action=action, description=description)

    except Exception as e:
        logger.error("❌ Error while executing the plugin: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()