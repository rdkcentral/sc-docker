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

from pathlib import Path

import yaml

class ConfigManager:
    """
    Manages configurations by loading from two YAML config files, merging a specific section,
    and allowing modifications only to the primary config.
    """

    def __init__(self, primary_config: str, secondary_config: str, section: str):
        """
        Initializes the ConfigManager, loading configuration files and merging a 
        specific section.

        Args:
            primary_config (str): Path to primary configuration file (modifiable).
            secondary_config (str): Path to secondary (read-only) configuration file.
            section (str): Section to merge and perform actions on.
        """        
        self.primary_config_path = Path(primary_config)
        self.secondary_config_path = Path(secondary_config)
        self.section = section
        
        self._primary_config = self._load_config(self.primary_config_path)
        self._secondary_config = self._load_config(self.secondary_config_path)

        self.merged_section = self._merge_section()
    
    def get_config(self) -> dict:
        """Returns the merged section."""
        return self.merged_section

    def update_config(self, updates: dict):
        """Updates the primary config's section and writes it back."""
        if self.section not in self._primary_config:
            self._primary_config[self.section] = {}

        self._primary_config[self.section].update(updates)

        self._save_primary_section()
        self.merged_section = self._merge_section()
    
    def delete_key_from_config(self, key: str) -> bool:
        """Deletes a key from the primary config's section and writes it back."""
        if self.section in self._primary_config and key in self._primary_config[self.section]:
            del self._primary_config[self.section][key]
            self._save_primary_section()
            self.merged_section = self._merge_section()
            return True
        return False

    def _load_config(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        return {}

    def _merge_section(self) -> dict:
        primary_section = self._primary_config.get(self.section, {})
        secondary_section = self._secondary_config.get(self.section, {})
        return {**secondary_section, **primary_section}

    def _save_primary_section(self):
        with open(self.primary_config_path, "w") as f:
            yaml.dump(self._primary_config, f, default_flow_style=False, sort_keys=False)

