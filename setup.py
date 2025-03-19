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

from setuptools import setup, find_packages

def read_version():
    with open("VERSION", "r") as f:
        return f.read().strip()

setup(
    name='sc-docker',
    python_requires=">=3.10",
    version=read_version(),
    author="RDK Management",
    description="An SC tool for finding and uniformly running docker images.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rdkcentral/sc-docker",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'Click',
        'requests==2.31.0', # Docker SDK breaks on 2.32.0
        'docker==7.1.0',
        'pyyaml==6.0.2',
        'sc @ git+https://github.com/rdkcentral/sc.git@main'
    ]
)