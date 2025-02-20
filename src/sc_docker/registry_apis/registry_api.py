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

class RegistryAPI(ABC):
    def name(self):
        name = self.__class__.__name__
        return getattr(self, "api_name", (name[:-3] if name.endswith("API") else name).lower())
    
    @abstractmethod
    def fetch_images(self, registry, username, token) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def fetch_tags(self, registry, username, token, container_name) -> tuple[str, ...]:
        raise NotImplementedError
