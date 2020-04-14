import argparse
import os
import shelve
from configparser import ConfigParser
from typing import Dict

from pysolate import CONFIG_FILE, CONFIG_PATH, config_defaults, AppConfig, log
from pysolate.container import build_container, executable, prepare_run_command, container_build_required, run_command


def parse_args():
    parser = argparse.ArgumentParser(description='Run containerized applications.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--reset', action='store_true', help='Replace stored settings with '
                                                                   'provided.')
    parser.add_argument('-d', '--pass-dir', dest='dir', action='store_true', help='Pass CWD to container.')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Run process in the terminal.')
    parser.add_argument('-t', '--no-pass-tmp', dest='no_tmp', action='store_true', help='Do not create shared folder '
                                                                                        'in '
                                                                                        '/tmp/{cmd}.')
    parser.add_argument('-u', '--uid', type=int, default=os.getuid(), help='UID of user to run process '
                                                                           'as. Defaults to current UID, '
                                                                           'assuming it exists in the '
                                                                           'container.')
    parser.add_argument('-U', '--update', action='store_true', help='Update the underlying container '
                                                                    'first.')
    parser.add_argument('-R', '--update-with-cache', action='store_true', help='Update the underlying image '
                                                                               'first, allowing the container '
                                                                               'engine to use its cache.')
    parser.add_argument('-p', '--no-persist', action='store_true', help="Don't persist files in "
                                                                        "home directory after "
                                                                        "session.")
    parser.add_argument('-V', '--verbose', action='store_true', help='Print detailed output.')
    parser.add_argument('-m', '--headless', action='store_true', help='No prompts. Useful for running from desktop shortcut.')
    parser.add_argument('-v', '--volume', action='append', default=[],
                        help='Mount additional volumes to container. Must provide '
                             'in format: <host_path>:<container_path>')
    parser.add_argument('-l', '--privileged', action='store_true', help='Use privileged mode.')
    parser.add_argument('-n', '--no-net', action='store_true', help='Disable all networking')
    parser.add_argument('command', default='bash', nargs='?', help='Command to run in container.')
    return parser.parse_args()


def create_default_config() -> None:
    if not os.path.isdir(CONFIG_PATH):
        for directory in (
                CONFIG_PATH,
                os.path.join(CONFIG_PATH, 'apps'),
                os.path.join(CONFIG_PATH, 'storage')):
            try:
                os.mkdir(directory)
            except FileExistsError:
                pass
    if not os.path.isfile(CONFIG_FILE):
        config = ConfigParser()
        config["pysolate"] = config_defaults
        with open(CONFIG_FILE, "w") as f:
            config.write(f)


def get_main_config() -> Dict:
    create_default_config()
    config = ConfigParser()
    with open(CONFIG_FILE) as f:
        config.read_file(f)
    return config


def load_shelf() -> shelve.Shelf:
    try:
        return shelve.open(os.path.join(CONFIG_PATH, 'data'))
    except OSError:
        log.error("Failed to open shelve config store. Maybe another instance has locked it? Bailing...")
        raise SystemExit


def get_cmd_config(cmd_key: str, args: argparse.Namespace) -> AppConfig:
    shelf = load_shelf()
    config = shelf.get(cmd_key)
    if not config or args.reset:
        config = AppConfig(args.command, args.dir, not args.no_tmp, args.uid,
                           not args.no_persist, args.interactive, args.privileged, args.volume)
        shelf[cmd_key] = config

    pass_dir = config.pass_dir or args.dir
    pass_tmp = config.pass_tmp and not args.no_tmp
    persist = config.persist and not args.no_persist
    interactive = config.interactive or args.interactive
    privileged = config.privileged or args.privileged
    volumes = set([*config.volumes, *args.volume])
    no_net = config.no_net or args.no_net

    shelf.close()
    return AppConfig(args.command, pass_dir, pass_tmp, args.uid, persist, interactive, privileged, volumes, no_net)


def main():
    if not executable:
        log.error("No suitable containerization engines found.")
        raise SystemExit
    args = parse_args()
    main_config = get_main_config()
    core_config = main_config['pysolate']

    if not args.headless and (args.update or args.update_with_cache or container_build_required()):
        build_container(core_config, args.update_with_cache)

    cmd_key = args.command.split(" ")[0]
    run_config = get_cmd_config(cmd_key, args)
    full_command = prepare_run_command(run_config, args.command, args.verbose)

    if args.verbose:
        log.info("Full command:", full_command)
        log.info("Running as user:", args.uid)
        log.info("Debug:", run_config.__dict__)
    run_command(full_command, run_config)


if __name__ == "__main__":
    main()
