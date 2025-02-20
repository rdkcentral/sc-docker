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

from .registry_api import RegistryAPI

from .artifactory import ArtifactoryAPI
from .github import GithubAPI

class RegistryAPIFactory:
    _registry_apis = {
        "artifactory": ArtifactoryAPI,
        "github": GithubAPI,
    }

    @classmethod
    def get_registry_api(cls, registry_type: str) -> RegistryAPI:
        api_class = cls._registry_apis.get(registry_type.lower())
        if not api_class:
            raise ValueError(f"Unknown registry type: {registry_type}")
        return api_class()

    @classmethod
    def get_supported_registry_types(cls) -> tuple:
        return tuple(cls._registry_apis)      
