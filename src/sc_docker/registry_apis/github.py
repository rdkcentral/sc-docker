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

class GithubAPI(RegistryAPI):
    reg_type = "Github"
    _BASE_URL: str = "https://api.github.com"

    def fetch_images(self, registry, username, token) -> tuple[str, ...]:
        org = registry.split('/')[-1]
        url = f"{self._BASE_URL}/orgs/{org}/packages?package_type=container"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        containers = []
        while url:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                page_containers = response.json()
                containers.extend([container['name'] for container in page_containers])

                link_header = response.headers.get('Link', '')
                url = response.links.get('next', {}).get('url')
            else:
                raise self.RegistryAPIException(self.reg_type, registry, response = response)
        
        return tuple(containers)

    def fetch_tags(self, registry, username, token, container_name) -> tuple[str, ...]:
        org = registry.split('/')[-1]
        url = f"{self._BASE_URL}/orgs/{org}/packages/container/{container_name}/versions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        tags = []
        while url:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                page_versions = response.json()
                for version in page_versions:
                    tags.append(version['metadata']['container']['tags'])

                # Check for pagination
                link_header = response.headers.get('Link', '')
                url = response.links.get('next', {}).get('url')
            else:
                raise self.RegistryAPIException(self.reg_type, registry, response = response)
        
        # Flatten the list of tags (since each version may have multiple tags)
        return tuple(tag for sublist in tags for tag in sublist)
