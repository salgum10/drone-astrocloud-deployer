drone-astrocloud-deployer
=========================

* Author: `Florian Dambrine <android.florian@gmail.com>`

Astrocloud deployer plugin to release new Astro projects packaged as Docker containers

# :notebook: Usage

* At least one example of usage

```yaml
---

# YAML Anchor to define common Astrocloud environment variables
astrocloud_env: &astrocloud_env
  environment:
    ORGANIZATION_ID:
      from_secret: astronomer_org_id
    DEPLOYMENT_ID:
      from_secret: astronomer_deployment_id
    ASTRONOMER_KEY_ID:
      from_secret: astronomer_key_id
    ASTRONOMER_KEY_SECRET:
      from_secret: astronomer_key_secret
    ASTRONOMER_API_TOKEN:
      from_secret: astronomer_api_token

pipeline:
  steps:
    - name: build-image
      image: public.ecr.aws/gumgum-verity/oss/astro-ap-build:0.2.0
      <<: *astrocloud_env
      commands:
        - docker build -t images.astronomer.cloud/$${ORGANIZATION_ID}/$${DEPLOYMENT_ID}:${DRONE_TAG:-${DRONE_COMMIT_SHA}} .

    - name: publish-image
      image: public.ecr.aws/gumgum-verity/oss/astro-ap-build:0.2.0
      <<: *astrocloud_env
      commands:
        - docker login images.astronomer.cloud -u $${ASTRONOMER_KEY_ID} -p $${ASTRONOMER_KEY_SECRET}
        - docker push images.astronomer.cloud/$${ORGANIZATION_ID}/$${DEPLOYMENT_ID}:${DRONE_TAG:-${DRONE_COMMIT_SHA}}

    - name: deploy-to-astrocloud
      image: lowess/drone-astrocloud-deployer
      settings:
        astronomer_api_token:
          from_secret: astronomer_api_token
        organization_id: <your-astronomer-org-id>
        deployment_id: <your-deployment-id>
        release_tag: ${DRONE_TAG:-${DRONE_COMMIT_SHA}}

```

---

# :gear: Parameter Reference

* `astronomer_api_token` _(required)_ (:lock: secret)
  * The Astrocloud API token to authenticate

* `organization_id` _(required)_
  * The [Astronomer Organization ID](https://docs.astronomer.io/astro/cli/astro-organization-list) that hosts the deployment to release to

* `deployment_id` _(required)_
  * The Databricks API Token to interract with your workspace

* `release_tag` _(required)_
  * The Databricks image tag to deploy to your Astrocloud deployment

* `dry_run` _(optional : default `false`)_
  * Whether to perform a dry run or not. If set to `true`, the plugin will not update the deployment with the new image tag

---

# :beginner: Development

* Run the plugin directly from a built Docker image:

```bash
docker run -i \
           -v $(pwd)/plugin:/opt/drone/plugin \
           -v ~/.aws:/root/.aws \
           -e PLUGIN_ORGANIZATION_ID=${ORGANIZATION_ID} \
           -e PLUGIN_DEPLOYMENT_ID=${DEPLOYMENT_ID} \
           -e PLUGIN_RELEASE_TAG=${RELEASE_TAG} \
           -e PLUGIN_ASTRONOMER_API_TOKEN=${ASTRONOMER_API_TOKEN} \
           lowess/drone-astrocloud-deployer
```
