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

from abc import ABC, abstractmethod

import requests

class RegistryAPI(ABC):
    reg_type = "NotImplemented"

    @abstractmethod
    def fetch_images(self, registry, username, token) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def fetch_tags(self, registry, username, token, container_name) -> tuple[str, ...]:
        raise NotImplementedError

    class RegistryAPIException(RuntimeError):
        def __init__(
                self, 
                registry_type: str,
                registry_url: str,
                response: requests.Response | None = None,
                message: str | None = None
            ):
            if response:
                try:
                    error_details = response.json()
                except ValueError:
                    error_details = response.text
                error_message = (
                    f"{registry_type} API {registry_url} error {response.status_code}: "
                    f"{error_details}"
                )
            elif message:
                error_message = f"{registry_type} API {registry_url} error: {message}"
            else:
                error_message = f"{registry_type} API {registry_url} error occured"
            
            super().__init__(error_message)
