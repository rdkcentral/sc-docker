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

import click

from .core import SCDocker

@click.group()
def cli():
    pass

@cli.command()
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

@cli.command()
def list():
    """List local and remote containers."""
    SCDocker().list_images()

@cli.command()
def login():
    """Login to a docker registry."""
    SCDocker().login()

@cli.command()
@click.argument('registry_url')
def logout(registry_url):
    """Logout of a docker registry."""
    SCDocker().logout(registry_url)

if __name__ == "__main__":
    cli()