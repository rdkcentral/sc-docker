# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests

from .registry_api import RegistryAPI

class ArtifactoryAPI(RegistryAPI):
    reg_type = "Artifactory"

    def fetch_images(self, registry, username, token) -> tuple[str, ...]:
        artifactory_root, repo = registry.split('/', 1)
        if not username:
            raise ValueError("Username is required for Artifactory API")

        url = f"https://{artifactory_root}/artifactory/api/docker/{repo}/v2/_catalog"
        response = requests.get(url, auth=(username, token))

        if response.status_code == 200:
            data = response.json()
            return tuple(data.get('repositories', ()))
        else:
            raise self.RegistryAPIException(self.reg_type, registry, response = response)

    def fetch_tags(self, registry, username, token, container_name) -> tuple[str, ...]:
        artifactory_root, repo = registry.split('/', 1)
        if not username:
            raise ValueError("Username is required for Artifactory API")

        url = f"https://{artifactory_root}/artifactory/api/docker/{repo}/v2/{container_name}/tags/list"
        response = requests.get(url, auth=(username, token))

        if response.status_code == 200:
            data = response.json()
            return tuple(data.get('tags', ()))
        else:
            raise self.RegistryAPIException(self.reg_type, registry, response = response)
