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

import getpass
import grp
from netrc import netrc, NetrcParseError
import os
from pathlib import Path
import subprocess
import sys
import time

import click
import docker
from docker.errors import APIError, TLSParameterError

from .registry_apis.registry_api_factory import RegistryAPIFactory
from sc.config_manager import ConfigManager

REGISTRY_WHITELIST = Path("/etc/sc/docker_registry_whitelist")

STANDARD_MOUNT_DIRS = ['/home/mirror', '/opt/repo_flow']
BANNED_MOUNT_DIRS = [
    "/boot", "/dev", "/etc", "/sys", "/proc", "/root", "/srv",
    "/bin", "/lib", "/lib32", "/lib64", "/libx32", "/run", "/sbin", "/tmp",
    "/var/run", "/var/lock", "/media", "/usr", "/mnt", "/snap"
]

class SCDocker:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.supported_registry_types = RegistryAPIFactory.get_supported_registry_types()


        self.docker_config_manager = ConfigManager('docker')
        self.docker_config = self.docker_config_manager.get_config()

        self.whitelisted_registries = self._get_whitelisted_registries()
        self._validate_existing_registries()

    def login(self):
        registry_url = self._prompt_registry_url()
        registry_type = self._prompt_registry_type()
        
        credential_store, username, api_token = self._prompt_credentials(registry_url)

        self._attempt_docker_login(username, api_token, registry_url)

        registry_api = RegistryAPIFactory.get_registry_api(registry_type)
        try:
            images = registry_api.fetch_images(registry_url, username, api_token)
        except Exception as e:
            click.secho(f"ERROR: An exception occured when fetching images from {registry_url}", fg='red')
            click.secho(e)
            sys.exit(1)
        self._validate_images(images, registry_url)
        
        self._update_user_config(registry_url, registry_type, credential_store, username, api_token)
        
        click.echo(f"\nRegistry {registry_url} has been added to your SC config!")
    
    def logout(self, registry_url: str):
        self.docker_config_manager.delete_key_from_config(registry_url)
        click.secho(f"Removed credentials for {registry_url}", fg="green", bold=True)
    
    def list_images(self):
        remote_images = []
        if self.docker_config:
            for registry_url in self.docker_config:
                registry_images = self._fetch_images_by_registry(registry_url)
                remote_images.extend([f"{registry_url}/{image}" for image in registry_images])
        
        # Get local image names and remove duplicates.
        local_images = list({tag.split(":")[0] for image in self.docker_client.images.list() for tag in image.tags})

        # Combine the lists while preserving order
        all_images = []
        seen = set()
        for image in remote_images + local_images:
            if image not in seen:
                all_images.append(image)
                seen.add(image)
        
        click.secho("Images are:- ", fg="green")
        remote_str = click.style(" (Remote)", fg="cyan")
        local_str = click.style(" (Local)", fg="magenta")

        for image in all_images:
            if image in remote_images and image in local_images:
                click.echo(click.style(image, fg="yellow", bold=True) + remote_str + local_str)
            elif image in remote_images:
                click.echo(click.style(image, fg="yellow", bold=True) + remote_str)
            elif image in local_images:
                click.echo(click.style(image, fg="yellow", bold=True) + local_str)

    def run(
            self, 
            image_ref: str, 
            command: tuple[str, ...], 
            local: bool, 
            tag: str, 
            x11: bool, 
            volumes: tuple[str, ...]
        ):
        self._check_no_registries(local)

        image = self._get_image(image_ref, local)
        registry_url, image_name = self._parse_image_reference(image)

        tags = self._fetch_tags(image, local, registry_url)
        if tag not in tags:
            self._handle_invalid_tag(image, tag, tags)

        if not local:
            username, api_token = self._get_registry_creds_by_url(registry_url)
            self.docker_client.login(username=username, password=api_token, registry=registry_url)
            self._pull_image(image, tag)
        
        container_name = self._generate_container_name(image_name)
        
        docker_command = self._generate_docker_run_command(image, tag, container_name, image_name, x11, volumes, command)

        self._execute_docker_run(docker_command, image)
    
    # ──────────────────────── REGISTRY & AUTH HELPERS ────────────────────────

    def _get_whitelisted_registries(self) -> tuple[str, ...]:
        if REGISTRY_WHITELIST.exists():
            with open(REGISTRY_WHITELIST, 'r') as file:
                return tuple(line.strip() for line in file)
        return ()
    
    def _validate_existing_registries(self):
        """Check if pre-existing registries in config are whitelisted. Exit if not."""
        if not self.whitelisted_registries:
            return

        invalid_registries = [r for r in self.docker_config if r not in self.whitelisted_registries]
        if invalid_registries:
            click.secho("ERROR: Some pre-configured registries are not in the whitelist!", fg="red")
            for registry in invalid_registries:
                click.echo(f"- {registry}")
            click.secho("\nAllowed registries:", fg="green")
            for reg in self.whitelisted_registries:
                click.echo(f"- {reg}")
            sys.exit(1)

    def _validate_registry_on_login(self, registry: str):
        if not self.whitelisted_registries or registry in self.whitelisted_registries:
            return

        click.secho(f"ERROR: Login attempt failed. {registry} is not whitelisted!", fg="red")
        click.secho("You can only log in to these registries:", fg="green")
        for reg in self.whitelisted_registries:
            click.echo(f"- {reg}")
        sys.exit(1)
    
    def _validate_images(self, images: list, registry_url: str):
        if not images:
            error_message = f"Registry {registry_url} returned no images! Check URL is correct!"
            click.secho(f"ERROR: {error_message}", fg="red", bold=True)
            sys.exit(1)
    
    def _get_registry_creds_by_url(self, registry_url: str) -> tuple[str, str]:
        registry_conf = self.docker_config[registry_url]
        if registry_conf['credential_store'] == "netrc":
            username, api_token = self._get_netrc_creds_by_registry(registry_url)
        else:
            username, api_token = registry_conf['username'], registry_conf['api_key']
        
        return username, api_token
    
    def _get_netrc_creds_by_registry(self, registry_url: str) -> tuple[str, str]:
        try:
            netrc_path = os.getenv('NETRC_PATH')
            creds = netrc(netrc_path) if netrc_path else netrc()

            if not creds:
                click.secho("ERROR: Failed to grab credentials from your .netrc", fg="red")
                click.secho("Netrc missing or empty!", fg='red')
                sys.exit(1)

            machine = registry_url.split("/")[0]
            auth = creds.authenticators(machine)
            if not auth:
                click.secho(f"ERROR: No authenticators found for machine '{machine}' in .netrc", fg="red")
                sys.exit(1)
            username, _, api_token = auth
            return username, api_token
        except NetrcParseError as e:
            click.secho("ERROR: Failed to grab credentials from your .netrc", fg="red")
            click.secho(f"Error message: {e}")
            click.secho("You may have to run command: chmod 600 ~/.netrc")
            sys.exit(1)
    
    def _attempt_docker_login(self, username: str, api_token: str, registry_url: str):
        try:
            self.docker_client.login(username=username, password=api_token, registry=registry_url)
        except (APIError, TLSParameterError) as e:
            click.secho("\nERROR: Failed to login with the credentials provided!", fg="red", bold="true")
            click.secho(f"Failed to login to Docker registry {registry_url}: {str(e)}", fg="red")
            sys.exit(1)

    def _update_user_config(self, registry_url: str, registry_type: str, credential_store: str, username: str, api_token: str):
        config_dict = { 
            registry_url: {      
                "reg_type": registry_type,
                "credential_store": credential_store,
            }
        }
        
        if credential_store == "config":
            config_dict[registry_url]["username"] = username
            config_dict[registry_url]["api_key"] = api_token

        try:
            self.docker_config_manager.update_config(config_dict)
        except Exception as e:
            error_message = f"Failed to write to the config: {str(e)}"
            click.secho(f"Error: {error_message}", fg="red", bold="true")
            sys.exit(1)

    # ──────────────────────── USER INPUT HELPERS ────────────────────────
    
    def _prompt_registry_url(self) -> str:
        click.echo("For a guide to logging in see: https://github.com/comcast-sky/sc-docker/blob/master/docs/pages/login.md")
        click.echo("Registry URL:")
        click.echo("- This should include the base URL and relevant namespace.")
        click.echo("Example (GitHub): ghcr.io/organisation")
        click.echo("Example (Artifactory): your.artifactory.com/docker-registry")

        registry_url = click.prompt("> ")
        self._validate_registry_on_login(registry_url)

        return registry_url

    def _prompt_registry_type(self) -> str:
        click.echo("\nRegistry Type:")
        while True:
            click.echo("Possible registry types:")
            for registry_type in self.supported_registry_types:
                click.echo(f"- {registry_type}")
            registry_type = click.prompt("> ")
            if registry_type in self.supported_registry_types:
                return registry_type
            click.echo("\nRegistry type not in possible registry types!")
    
    def _prompt_credentials(self, registry_url: str) -> tuple[str,str,str]:
        """Prompt user for credentials, either from .netrc or manual input."""
        click.echo("\nUse netrc? (y/n):")
        click.echo("- Choosing 'y' will allow SC to use credentials stored in your .netrc file.")
        click.echo("- Choose 'n' if you prefer to enter your username and API key manually.")
        
        netrc_input = click.prompt("> ")
        
        if netrc_input == "y":
            credential_store = "netrc"
            username, api_token = self._get_netrc_creds_by_registry(registry_url)
        else:
            credential_store = "config"
            click.echo("\nUsername:")
            click.echo("For GitHub, this is usually your GitHub username or email")
            click.echo("For Artifactory, use your Artifactory username.")
            username = click.prompt("> ")

            click.echo("\nAPI Key")
            click.echo("- For GitHub, this is your personal access token.")
            click.echo("- For Artifactory, this is your API key.")
            api_token = click.prompt("> ")

        return credential_store, username, api_token
    
    # ──────────────────────── IMAGE & CONTAINER HANDLING HELPERS ────────────────────────

    def _get_image(self, image_ref: str, local: bool) -> str:
        """Get the full image name from a reference

        Args:
            image_ref (str): An image reference, either the full name or with the
            registry part removed.
            local (bool): True if looking for a local image

        Returns:
            str: The full image name
        """        
        images = []
        
        if local:
            images = list({tag.split(":")[0] for image in self.docker_client.images.list() for tag in image.tags})
        else:
            # If image ref matches a host just get that hosts images. Otherwise get all hosts images.
            host = False
            for registry_url in self.docker_config:
                if image_ref.startswith(registry_url):
                    host = registry_url

            if host:
                images = [f"{host}/{image}" for image in self._fetch_images_by_registry(host)]
            else:
                for registry_url in self.docker_config:
                    registry_images = self._fetch_images_by_registry(registry_url)
                    images.extend([f"{registry_url}/{image}" for image in registry_images])
        
        valid_images = []
        for image in images:
            if image.endswith(image_ref):
                valid_images.append(image)
                
        if len(valid_images) == 1:
            image_to_run = valid_images[0]
        elif len(valid_images) > 1:
            image_to_run = valid_images[0]
            click.secho("WARNING!", fg="red", bold=True)
            click.secho(f"Your image {image_ref} matched multiple images", fg="red", bold=True)
            click.secho(f"SC docker has chosen to run image {image_to_run}", fg="red", bold=True)
            click.secho("If you want to run a different image use its full image name", fg="red", bold=True)
            click.secho("Image's matched:", fg="yellow", bold=True)
            for image in valid_images:
                click.secho(image, fg="yellow", bold=True)
        else:
            click.secho(f"Image {image_ref} matched no known images!", fg="red", bold=True)
            self.list_images()
            sys.exit(1)

        return image_to_run
    
    def _pull_image(self, image:str, tag:str):
        layer_progress = {}
        try:
            for line in self.docker_client.api.pull(image, tag, stream=True, decode=True):
                if 'id' in line:
                    layer_id = line['id']
                    status = line.get('status', '')
                    progress = line.get('progress', '')

                    layer_progress[layer_id] = (status, progress)
                    for layer_id in layer_progress.keys():
                        status, progress = layer_progress[layer_id]
                        if progress == '':
                            sys.stdout.write(f"{layer_id[:12]}: {status} {' ' * 80}\n")
                        else:
                            sys.stdout.write(f"{layer_id[:12]}: {status} {progress.ljust(40)}\n")

                    sys.stdout.flush()
                    sys.stdout.write("\033[F" * len(layer_progress))  # Move the cursor up for each layer

                elif 'error' in line:
                    sys.stdout.write(f"\nError: {line['error']}\n")
                    sys.stdout.flush()
            
            sys.stdout.write("\033[999B") # Move the cursor to the very bottom
            sys.stdout.flush()
            click.secho("Pull complete!\n")
        except KeyboardInterrupt:
            sys.stdout.write("\033[999B")
            sys.stdout.flush()
            click.secho("ERROR: Pull interrupted by keyboard.", fg='red', bold=True)
            sys.exit(1)
        except APIError as e:
            sys.stdout.write("\033[999B")
            sys.stdout.flush()
            click.secho(f"\nDocker API error: {e.explanation}\n")
            click.secho("ERROR: Unable to pull the image due to a Docker API error.", fg='red', bold=True)
            sys.exit(1)
        except Exception as e:
            sys.stdout.write("\033[999B")
            sys.stdout.flush()
            click.secho(f"\nUnexpected error: {str(e)}\n")
            click.secho("ERROR: An unexpected error occurred.", fg='red', bold=True)
            sys.exit(1)

    def _fetch_tags(self, image: str, local: bool, registry_url: str) -> tuple[str, ...]:
        if local:
            return self._fetch_local_tags(image)
        
        username, api_token = self._get_registry_creds_by_url(registry_url)
        return self._fetch_remote_tags(image, username, api_token)

    def _fetch_local_tags(self, image: str):
        local_images = self.docker_client.images.list()
        tags = []
        
        for local_image in local_images:
            for tag in local_image.tags:
                name_part = tag.split(":")[0]
                if name_part == image:
                    tags.append(tag.split(":")[1])
        return tuple(tags)
    
    def _fetch_remote_tags(self, image: str, username: str, api_token: str) -> tuple[str, ...]:
        registry_url, image_name = self._parse_image_reference(image)
        registry_type = self.docker_config[registry_url]['reg_type']
        registry_api = RegistryAPIFactory.get_registry_api(registry_type)

        try:
            return registry_api.fetch_tags(registry_url, username, api_token, image_name)
        except Exception as e:
            click.secho(
                f"ERROR: An exception occured when fetching tags for image {image_name} from {registry_url}",
                fg='red')
            click.secho(e)
            sys.exit(1)

    def _fetch_images_by_registry(self, registry_url: str) -> tuple[str, ...]:
        username, api_token = self._get_registry_creds_by_url(registry_url)
        registry_type = self.docker_config[registry_url]['reg_type']
        registry_api = RegistryAPIFactory.get_registry_api(registry_type)
        try:
            return registry_api.fetch_images(registry_url, username, api_token)
        except Exception as e:
            click.secho(f"ERROR: An exception occured when fetching images from {registry_url}", fg='red')
            click.secho(e)
            sys.exit(1)
    
    def _handle_invalid_tag(self, image:str, tag: str, tags: tuple[str, ...]):
        click.echo(
            click.style("ERROR: ", fg="red", bold = True) +
            click.style(f"Expected tag '{tag}' not found for image '{image}'", fg="red")
        )
        click.echo(f"Available tags for {image}:")
        for t in tags:
            click.echo(t)
        sys.exit(1)

    def _check_no_registries(self, local: bool):
        if not local and not self.docker_config:
            click.secho(
                "WARNING: You have not logged into any registries and therefore can only use",
                fg = 'red', bold=True)
            click.secho(
                "`sc docker run` with the --local tag! Use `sc docker login` to add remote registries!",
                fg = 'red', bold=True)
            sys.exit(1)
    
    def _generate_container_name(self, image_name: str) -> str:
        """Add UNIX username and time since epoch to name so we can see who created a container and when"""
        user_name = getpass.getuser()
        
        seconds_since_epoch = int(time.time())
        nanoseconds = int(time.time_ns() % 1e9)
        time_since_epoch = f"{seconds_since_epoch}-{nanoseconds}"
        container_name = f"{user_name}_{image_name}_{time_since_epoch}"
        return container_name
    
    def _parse_image_reference(self, image: str) -> tuple[str, str]:
        """Split image reference into registry url and image name"""
        last_slash = image.rfind("/")
        registry_url = image[:last_slash]
        image_name = image[last_slash+1:]
        return registry_url, image_name

    # ──────────────────────── DOCKER RUN HELPERS ────────────────────────

    def _generate_docker_run_command(
            self, 
            image: str, 
            tag: str, 
            container_name: str, 
            image_name: str, 
            x11: bool, 
            volumes: tuple[str, ...], 
            command: tuple[str, ...]
        ) -> list:
        """Generates the full docker run command."""
        docker_args = ['docker', 'run', '--rm']

        docker_args += ['--net=host']
        docker_args += ['-v', f"{Path.home()}:{Path.home()}"]
        docker_args += ['--name', container_name, '--hostname', image_name]

        docker_args += self._get_architecture_flag(image)
        docker_args += self._add_volume_mounts(volumes)
        docker_args += self._add_ssh_auth()
        docker_args += self._add_x11_support() if x11 else []
        docker_args += self._add_user_env_vars()
        docker_args += self._add_interactive_flag()

        docker_args += [f"{image}:{tag}", self._generate_bash_command(command, container_name, x11)]
        return docker_args
    
    def _generate_bash_command(
            self, 
            command: tuple[str, ...], 
            container_name: str, 
            x11: bool
        ) -> str:
        """Generates the bash command to be executed inside the container."""
        bash_command = f"source /usr/local/bin/bashext.sh && cd {Path.cwd()}; "
        if x11 and os.getenv("DISPLAY"):
            bash_command += self._setup_xauth(container_name)
        return bash_command + " ".join(command)
    
    def _execute_docker_run(self, docker_command: list, image: str):
        """Prints and executes the docker run command."""
        docker_command_str = " ".join(docker_command)
        click.secho(f"Running docker [{image}]", fg='green')
        click.secho(docker_command_str, fg='green')
        click.echo()
        os.execvp('docker', docker_command)

    def _get_architecture_flag(self, image: str) -> list:
        architecture = image.split("_")[-1]
        if architecture == 'i386':
            return ['--platform', 'linux/i386']
        elif architecture == 'amd64':
            return ['--platform', 'linux/amd64']
        return []

    def _add_volume_mounts(self, volumes: tuple[str, ...]) -> list:
        docker_args = []
        for volume in volumes:
            self._validate_docker_mount(volume)
            docker_args += ['-v', volume]
        
        for path in STANDARD_MOUNT_DIRS:
            if Path(path).exists():
                docker_args += ['-v', f"{path}:{path}"]

        codesonar_dir = Path('/opt/codesonar').resolve()
        if Path('/opt/codesonar').is_symlink() and Path(codesonar_dir).exists():
            docker_args += ['-v', f"{codesonar_dir}:{codesonar_dir}"]
            docker_args += ['-e', f"CODESONAR_PATH={codesonar_dir}/codesonar/bin"]

        return docker_args

    def _validate_docker_mount(self, mount: str):
        # Expect exactly one ':' character separating source and destination
        parts = mount.split(":")
        if len(parts) != 2:
            click.secho(f"WARNING: {mount} is not valid syntax for a mount", fg='red')
            sys.exit("Mounts are expected as -v <source directory>:<destination directory>")
        
        mount_source, mount_dest = parts
        self._validate_docker_mount_source(mount_source)
        self._validate_docker_mount_dest(mount_dest)

    def _validate_docker_mount_source(self, server_dir: str):
        if not os.path.isdir(server_dir):
            sys.exit(f"{server_dir} does not exist")
        
        stat_info = os.stat(server_dir)
        user = getpass.getuser()
        group = grp.getgrgid(stat_info.st_gid).gr_name
        
        # Check if others have write permission
        if stat_info.st_mode & 0o002:
            return
        
        # Check if the user is the owner and has write permission
        if os.getenv("USER") == user and (stat_info.st_mode & 0o200):
            return
        
        # Check if the user is in the group and has write permission
        user_groups = [g.gr_name for g in grp.getgrall() if os.getenv("USER") in g.gr_mem]
        if group in user_groups and (stat_info.st_mode & 0o020):
            return
        
        click.secho(f"WARNING: You cannot mount {server_dir}", fg='red')
        click.secho("You can only mount directories you have write permissions to", fg='red')
        sys.exit(1)

    def _validate_docker_mount_dest(self, dest_dir: str):        
        if any(dest_dir.startswith(root) for root in BANNED_MOUNT_DIRS):
            click.secho(f"WARNING: You cannot mount to {dest_dir}",
                                   fg='red')
            sys.exit(f"You cannot mount in any of the following directories: {', '.join(BANNED_MOUNT_DIRS)}")

    def _add_ssh_auth(self) -> list:
        docker_args = []
        ssh_auth_sock = os.getenv("SSH_AUTH_SOCK")
        if ssh_auth_sock:
            docker_args += [
                '-v',
                f"{Path(ssh_auth_sock).parent}:{Path(ssh_auth_sock).parent}",
                '-e',
                f"SSH_AUTH_SOCK={ssh_auth_sock}"
            ]
        return docker_args

    def _add_x11_support(self) -> list:
        docker_args = []
        if os.getenv("DISPLAY"):
            docker_args += ['-e', 'DISPLAY']
        else:
            click.secho("WARNING: No DISPLAY variable set", fg="yellow")
            click.secho("WARNING: X11 not forwarded into docker", fg="yellow")
        return docker_args

    def _setup_xauth(self, container_name: str) -> str | None:
        display = os.getenv("DISPLAY")
        try:
            xauth_line = subprocess.check_output(
                ["xauth", "list", display],
                stderr=subprocess.DEVNULL
                ).strip().decode()
        except subprocess.CalledProcessError:
            xauth_line = None
        
        if xauth_line:
            hostname = os.getenv("HOSTNAME")
            xauth_line = f"{xauth_line}/{hostname}/{container_name}"
            return f"touch {Path.home()}/.Xauthority; xauth add {xauth_line}; "
    
    def _add_user_env_vars(self) -> list:
        docker_args = [
            '-e', f"LOCAL_USER_NAME={getpass.getuser()}",
            '-e', f"LOCAL_USER_ID={os.getuid()}",
            '-e', f"LOCAL_GROUP_ID={os.getgid()}",
            '-e', f"LOCAL_START_DIR={Path.home()}",
        ]
        try:
            docker_group_id = grp.getgrnam('docker').gr_gid
            docker_args += ['-e', f"LOCAL_DOCKER_GROUP={docker_group_id}"]
        except:
            pass
        return docker_args

    def _add_interactive_flag(self) -> list:
        # If stdout is connected to a terminal
        return ['-it'] if os.isatty(sys.stdout.fileno()) else []
