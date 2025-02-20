<div align="center">

# sc-docker
### Software Control (sc) Docker Plugin
![language](https://img.shields.io/badge/language-python-239120)
![OS](https://img.shields.io/badge/OS-linux%2C%20macOS-0078D4)

The sc docker module allows users to run docker containers in a standardised manner, using known docker registries. 

</div>

## Table of Contents
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Usage](#usage)
  - [Design Doc](#design-doc)

## Requirements

* Install Python 3.10+
* The docker engine must be installed.
    * Installation instructions can be found [here](https://docs.docker.com/engine/install/)
* Access to the docker engine
    * Access to the docker engine, could require privileged permissions, on linux it requires the user to be part of the docker group. See installation instructions above for more about this.
* Install SC 
    * `pip install git+https://github.com/rdkcentral/sc.git@main`

## Installation

`pip install git+https://github.com/rdkcentral/sc-docker.git@main`

## Quick Start

To work with private Docker registries, such as those used within our projects, you need to securely log in and store your credentials. Here's how:

* `sc docker login`
    * VIEW THE [LOGIN GUIDE!](docs/pages/login.md)
    * Enter your registry e.g. ghcr.io/comcast-sky
    * Enter your registry type e.g. github
    * Are your credentials in your netrc? e.g n
    * Enter username
    * Enter API key
* Use `sc docker list` to find available dockers
* `sc docker run` docker_name command

## Usage

The usage document provides examples demonstrating the functionality of the module, which you can reference here: [Usage Manual](./docs/pages/usage.md)

## Admin Tools

* To whitelist registries write them in the directory /etc/sc/docker_registry_whitelist seperated by newlines.
* To set server-wide registry logins add them to /etc/sc/.config.yaml in the following format:
```yaml
docker:
  ghcr.io/your-org:
    reg_type: github
    credential_store: config
    username: your_username
    api_key: your_api_key
```
