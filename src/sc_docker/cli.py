#!/usr/bin/env python3
#
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

import subprocess
import sys

import click

from .core import SCDocker

@click.group()
def cli():
    # Putting functionality in here will do nothing as sc entrypoint now
    # loads groups and commands under this group directly bypassing it.
    pass

@cli.group()
def docker():
    """Run and manage dockers."""
    _validate_docker()

@docker.command()
@click.argument('image')
@click.argument('command', nargs=-1, required=False)
@click.option('-l', '--local', is_flag=True, help='Run a local image.')
@click.option('-t', '--tag', default='latest', help='Image tag.')
@click.option('--x11', is_flag=True, help='Forward X11 into the docker.')
@click.option('-v', '--volume', multiple=True, help='Mount a volume.')
def run(
        image: str, 
        command: tuple[str, ...], 
        local: bool, 
        tag: str, 
        x11: bool, 
        volume: tuple[str, ...]
    ):
    """Run a docker using its name or its URL and name."""
    SCDocker().run(
        image_ref=image, 
        command=command, 
        local=local, 
        tag=tag, 
        x11=x11, 
        volumes=volume
    )

@docker.command()
def list():
    """List local and remote containers."""
    SCDocker().list_images()

@docker.command()
def login():
    """Login to a docker registry."""
    SCDocker().login()

@docker.command()
@click.argument('registry_url')
def logout(registry_url):
    """Logout of a docker registry."""
    SCDocker().logout(registry_url)

def _validate_docker():
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        click.secho("ERROR: Docker not installed or not in path!", fg="red")
        sys.exit(1)

    try:
        subprocess.run(["docker", "ps"], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        click.secho(f"ERROR: Docker failed: {e}", fg="red")
        click.secho(f"You likely don't have access to the docker daemon!", fg="red")
        sys.exit(1)

if __name__ == "__main__":
    cli()