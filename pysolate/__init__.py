import argparse
import os
import shelve
import subprocess


class Config:
    def __init__(self, full_command: str, pass_dir: bool = False, pass_tmp: bool = True,
                 uid: int = 1000, persist: bool = True, interactive: bool = False):
        self.full_command = full_command
        self.pass_dir = pass_dir
        self.uid = uid
        self.persist = persist
        self.tmp = pass_tmp
        self.interactive = interactive


def main():
    storage_location = os.path.expanduser('~/.config/pysolate')
    run_command = """sudo docker run --rm -it \
    {} {} \
    -e DISPLAY=unix{} \
    --device /dev/snd contain {}"""

    parser = argparse.ArgumentParser(description='Run containerized applications.')
    parser.add_argument('-r', '--reset', dest='reset', action='store_true', help='Replace stored settings with '
                                                                                 'provided.')
    parser.add_argument('-d', '--pass-dir', dest='dir', action='store_true', help='Pass CWD to container.')
    parser.add_argument('-i', '--interactive', dest='interactive', action='store_true',
                        help='Run process in the terminal.')
    parser.add_argument('-t', '--no-pass-tmp', dest='no_tmp', action='store_true', help='Do not create shared folder '
                                                                                        'in '
                                                                                        '/tmp/{cmd}.')
    parser.add_argument('-u', '--uid', dest='uid', type=int, default=1000, help='UID of user to run process as.')
    parser.add_argument('-p', '--no-persist', dest='no_persist', action='store_true', help="Don't persist files in "
                                                                                           "home directory after "
                                                                                           "session.")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Print detailed output.')
    parser.add_argument('command', default='bash', nargs='?', help='Command to run in container.')
    args = parser.parse_args()

    if not os.path.isdir(storage_location):
        for directory in (
                storage_location,
                os.path.join(storage_location, 'apps'),
                os.path.join(storage_location, 'storage')):
            try:
                os.mkdir(directory)
            except FileExistsError:
                pass
    shelf = shelve.open(os.path.join(storage_location, 'data'))
    cmd_key = args.command.split(" ")[0]
    config = shelf.get(cmd_key)
    if not config or args.reset:
        config = Config(args.command, args.dir, not args.no_tmp, args.uid,
                        not args.no_persist, args.interactive)
        shelf[cmd_key] = config
    pass_dir = config.pass_dir or args.dir
    pass_tmp = config.tmp and not args.no_tmp
    persist = config.persist and not args.no_persist
    interactive = config.interactive or args.interactive
    shelf.close()

    extras = ["-u {}".format(args.uid)]
    volumes = ["/tmp/.X11-unix:/tmp/.X11-unix",
               "{}:/apps".format(os.path.join(storage_location, 'apps'))
               ]

    if pass_dir:
        volumes.append('{}:/cwd'.format(os.getcwd()))
        if args.verbose:
            print("Passing CWD to process.")

    if pass_tmp:
        shared_dir = '.pysolate_{}'.format(cmd_key)
        try:
            os.mkdir(os.path.join('/', 'tmp', shared_dir))
        except FileExistsError:
            pass
        volumes.append('/tmp/{}:/share'.format(shared_dir))
        if args.verbose:
            print("Passing /tmp/{} to /share.".format(shared_dir))

    if persist:
        try:
            os.mkdir(os.path.join(storage_location, 'storage', args.command))
        except FileExistsError:
            pass
        volumes.append('{}:/home/user'.format(os.path.join(storage_location, 'storage', args.command)))
        if args.verbose:
            print("Using temporary filesystem.")
    else:
        if args.verbose:
            print("Using persistent filesystem.")

    cmd = run_command.format('-v ' + ' -v '.join(volumes), ' '.join(extras), os.environ['DISPLAY'], args.command)
    if args.verbose:
        print("Full command:", cmd)
        print("Running as user:", args.uid)
        print("Debug:", config.__dict__)
    if interactive:
        os.system(cmd)
    else:
        os.system('sudo -S true')
        subprocess.Popen(cmd, stderr=subprocess.DEVNULL, shell=True)
