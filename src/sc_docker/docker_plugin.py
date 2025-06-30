from .cli import cli
from sc.plugin import Plugin 

class DockerPlugin(Plugin):
    def get_cli(self):
        return cli

    # This is an example sc-docker doesn't use logging in its current state.
    @property
    def loggers_to_register(self):
        return ['docker']