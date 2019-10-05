import os
import re
import subprocess
from shutil import which
from tempfile import NamedTemporaryFile
from typing import Dict

from pysolate import AppConfig, CONFIG_PATH, get_config_value, log

build_template = """FROM {base_image}
ENV HOME /home/{username}
RUN useradd --shell /bin/bash --create-home --home-dir $HOME {username} --uid {uid} \
                                           && chown -R {username}:{username} $HOME
ENV PATH "$PATH:/apps"

WORKDIR $HOME
RUN mkdir -p /usr/share/man/man1/
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get dist-upgrade -y \
    && apt-get install -y --no-install-recommends {packages}
USER {username}
"""

DOCKER_EXEC = which('docker')
PODMAN_EXEC = which('podman')
IMAGE_NAME = 'k3an3/contain'
RUN_COMMAND = """{} run --rm -it \
{} {} \
-e DISPLAY=unix{} \
--device /dev/snd {} {}"""


def get_container_executable() -> str:
    if DOCKER_EXEC:
        return 'sudo ' + DOCKER_EXEC
    elif PODMAN_EXEC:
        return PODMAN_EXEC
    return None


executable = get_container_executable()


def build_container(config: Dict, cache: bool = False) -> None:
    base_image = get_config_value(config, 'base_image')
    try:
        subprocess.run([executable, 'pull', base_image], check=True)
    except subprocess.CalledProcessError:
        log.error(f"Unable to pull base image '{base_image}'. Bailing...")
        raise SystemExit
    with NamedTemporaryFile(mode="w+") as tf:
        tf.write(build_template.format(**config))
        tf.seek(0)
        build_command = [executable, 'build']
        if not cache:
            build_command.append('--no-cache')
        build_command.extend(['-t', IMAGE_NAME, '-f', tf.name])
        try:
            subprocess.run(build_command, check=True)
        except subprocess.CalledProcessError:
            log.error(f"Failed to build {IMAGE_NAME}. Bailing...")
            raise SystemExit
    log.success("Built", IMAGE_NAME, "successfully.")


def container_build_required() -> bool:
    out = subprocess.run([*executable.split(), 'images'], capture_output=True).stdout.decode()
    for line in out.split('\n'):
        if IMAGE_NAME in line:
            age = re.search(r'([0-9]+) weeks ago', line)
            if age and int(age.group(1)) > 2:
                answer = input("Image is {} weeks old, perform update? [Y/n]: ")
                if answer.lower() in ['', 'y']:
                    break
            return False
    return True


def prepare_run_command(config: AppConfig, full_command: str, verbose: bool) -> str:
    extras = ["-u {}".format(config.uid)]
    volumes = ["/tmp/.X11-unix:/tmp/.X11-unix",
               "{}:/apps".format(os.path.join(CONFIG_PATH, 'apps')),
               *config.volumes
               ]

    if config.pass_dir:
        volumes.append('{}:/cwd'.format(os.getcwd()))
        if verbose:
            log.info("Passing CWD to process.")

    if config.pass_tmp:
        shared_dir = '.pysolate_{}'.format(config.get_key())
        try:
            os.mkdir(os.path.join('/', 'tmp', shared_dir))
        except FileExistsError:
            pass
        volumes.append('/tmp/{}:/share'.format(shared_dir))
        if verbose:
            log.info("Passing /tmp/{} to /share.".format(shared_dir))

    if config.persist:
        try:
            os.mkdir(os.path.join(CONFIG_PATH, 'storage', config.get_key()))
        except FileExistsError:
            pass
        volumes.append('{}:/home/user'.format(os.path.join(CONFIG_PATH, 'storage', config.get_key())))
        if verbose:
            log.info("Using temporary filesystem.")
    else:
        if verbose:
            log.info("Using persistent filesystem.")

    if config.privileged:
        if verbose:
            log.info("Privileged mode.")
        extras.append('--privileged')
        extras.append('--net=host')

    if config.no_net:
        if verbose:
            log.info("Disabling networking.")
        extras.append("--net=none")

    if 'podman' in executable:
        extras.append('--userns=keep-id')

    return RUN_COMMAND.format(executable, '-v ' + ' -v '.join(volumes),
                              ' '.join(extras), os.environ['DISPLAY'],
                              IMAGE_NAME, full_command)


def run_command(command: str, config: AppConfig) -> None:
    if 'sudo' in command:
        os.system('sudo -S true')
    if config.interactive:
        subprocess.run(command, shell=True)
    else:
        subprocess.run(command, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, shell=True)
