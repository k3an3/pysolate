import argparse
import os


def main():
    storage_location = os.path.expanduser('~/.config/pysolate')
    run_command = """sudo docker run --rm -it \
    {} {} \
    -e DISPLAY=unix{} \
    --device /dev/snd contain {}"""

    parser = argparse.ArgumentParser(description='Run containerized applications.')
    parser.add_argument('-d', '--pass-dir', dest='dir', action='store_true', help='Pass CWD to container.')
    parser.add_argument('-u', '--uid', dest='uid', type=int, default=1000, help='UID of user to run process as.')
    parser.add_argument('-p', '--no-persist', dest='no_persist', action='store_true', help='UID of user to run '
                                                                                           'process as.')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Print detailed output.')
    parser.add_argument('command', default='bash', nargs='?', help='Command to run in container.')
    args = parser.parse_args()

    if not os.path.isdir(storage_location):
        for directory in (storage_location, os.path.join(storage_location, 'apps'), os.path.join(storage_location, 'storage')):
            try:
                os.mkdir(directory)
            except FileExistsError:
                pass
    # shelf = shelve.open(os.path.join(storage_location, 'data'))
    # shelf.close()

    extras = ["-u {}".format(args.uid)]
    volumes = ["/tmp/.X11-unix:/tmp/.X11-unix",
               "{}:/apps".format(os.path.join(storage_location, 'apps'))
               ]

    if args.dir:
        volumes.append('{}:/cwd'.format(os.getcwd()))

    if not args.no_persist:
        try:
            os.mkdir(os.path.join(storage_location, 'storage', args.command))
        except FileExistsError:
            pass
        volumes.append('{}:/home/user'.format(os.path.join(storage_location, 'storage', args.command)))

    cmd = run_command.format('-v ' + ' -v '.join(volumes), ' '.join(extras), os.environ['DISPLAY'], args.command)
    if args.verbose:
        print("Full command:", cmd)
    os.system(cmd)
