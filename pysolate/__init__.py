import os
from typing import Any, Dict, List

import colorful

CONFIG_PATH = os.path.expanduser('~/.config/pysolate')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.ini')

config_defaults = {
    'base_image': 'debian:stable-slim',
    'packages': '',
    'username': 'user',
    'uid': os.getuid(),
    'gid': os.getgid()
}


def get_config_value(config: Dict, key: str) -> Any:
    """
    Given a key for a config param, return the value from the supplied config dict, or the default.
    :param config: A dictionary/config object
    :param key: The config key
    :return: The resolved config value
    """
    return config.get(key, config_defaults[key])


class AppConfig:
    """
    An AppConfig stores configuration paramaters that apply to an individual containerized application (e.g.
    "firefox"). These values may be stored persistently with shelve, and can be overridden/modified at runtime.
    """

    def __init__(self, full_command: str, pass_dir: bool = False, pass_tmp: bool = True,
                 uid: int = 1000, persist: bool = True, interactive: bool = False,
                 privileged: bool = False, volumes: List = []):
        self.full_command = full_command
        self.pass_dir = pass_dir
        self.uid = uid
        self.persist = persist
        self.pass_tmp = pass_tmp
        self.interactive = interactive
        self.privileged = privileged
        self.volumes = volumes

    def get_key(self) -> str:
        """
        Return a string that identifies this command, consisting of the command's argv[0].
        :return: A unique key identifying this command.
        """
        return self.full_command.split(" ")[0]


class Log:
    prefix = "[{}]"

    def _print(self, symbol: str, *args, **kwargs):
        print(self.prefix.format(symbol), *args, **kwargs)

    def info(self, *args, **kwargs):
        self._print(colorful.blue("*"), *args, **kwargs)

    def success(self, *args, **kwargs):
        self._print(colorful.green("+"), *args, **kwargs)

    def error(self, *args, **kwargs):
        self._print(colorful.red("-"), *args, **kwargs)


log = Log()
