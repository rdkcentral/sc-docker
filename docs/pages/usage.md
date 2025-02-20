# Usage

## `sc docker help`

### Synopsis

`sc docker help|usage`

### Description 

This command displays help and usage information.

## `sc docker login`

### Synopsis

`sc docker login`

### Description

After using this command you will be prompted for different options for your login.

- Registry to login: This should be a registry not just a host, for example ghcr.io/registry instead of just ghcr.io
- Registry type: Currently the supported registry types are `github` or `artifactory`
- Credential store: The options are `config` or `netrc`, choose config if you want to input your credentials manually or choose netrc to have your credentials read from your netrc
- Username/Api Key: This is only asked if you chose `config`, manually enter your username and api key for the registry

### Obtaining Credentials

##### GitHub Container Registry (GHCR):

To create a Personal Access Token (PAT) for GitHub, follow the instructions [here.](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic)

##### Artifactory:

Currently, we use API Keys to access Artifactory. Find yours by:
- Clicking your profile icon in the top-right corner.
- Selecting Edit Profile.
- Scrolling down to API Key.

Note: Artifactory will transition to using Personal Access Tokens in Q4 2024. We will update this guide with the new instructions at that time.

## `sc docker logout`

### Synopsis

`sc docker logout <registry>`

### Description

Removes your login details from being stored in your registry config.

## `sc docker run` 

### Synopsis

`sc docker run [SWITCH] <image> [OPTIONS] <command>`

### Description

This command executes the named docker image and supplies the arguments to it. 

### SWITCH

* `--local` - Start a docker container of a local docker image. 

  > Example: `sc docker run --local rdk-core "echo hello" `
  >
  > This will start a container of the local image called 'ada-sdk' and execute the command '"echo hello"'.

* `help|--help|-h` - Display the help and usage information for `sc docker run`

### OPTIONS

* `-v <host directory>:<container directory> ` - Mount a directory from the host to the container. 

  > Example: `sc docker run rdk-core -v /opt/test:/home/test bash`
  >
  > This will mount the `/opt/test/` directory from the host, into the docker container as the `/home/test/` directory. 
  > Files modified with in the mounted directory will be modified on the host
  >
  > *It is not permitted to mount to the following container directories:*
  > * /boot 
  > * /dev
  > * /etc
  > * /sys
  > * /proc
  > * /root
  > * /srv
  > * /bin
  > * /lib
  > * /lib32
  > * /lib64
  > * /libx32
  > * /run
  > * /sbin
  > * /tmp
  > * /var/run
  > * /var/lock
  > * /media
  > * /usr
  > * /mnt
  > * /snap

* `-t <tag>` - Use a specific tagged version of the docker image.

  > Example: `sc docker run rdk-core -t 1.0 bash`
  >
  > This will pull and run a container of the rdk-core docker image, tagged with the `1.0` tag. 
* `--x11` - Allows x11 forwarding from inside the docker container.

  > Example: `sc docker run rdk-core --x11 bash`
  >
  > This will run a container of the rdk-core docker image and set it up to allow x11 forwarding back to the users display.
  >
  > *The user must already have an x11 display setup to use this*




## `sc docker list`

### Synopsis

`sc docker list`

### Description  

This command will list all available docker images.

