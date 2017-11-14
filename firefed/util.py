import argparse
from collections import OrderedDict
from configparser import ConfigParser
from datetime import datetime
import os
from pathlib import Path

import firefed.__version__ as version


class ProfileNotFoundError(Exception):

    def __init__(self, name):
        super().__init__('Profile "%s" not found.' % name)


def profile_dir(name):
    """Return path to FF profile for a given profile name or path."""
    if name:
        possible_path = Path(name)
        if possible_path.exists():
            return possible_path
    mozilla_dir = Path('~/.mozilla/firefox').expanduser()
    config = ConfigParser()
    config.read(mozilla_dir / 'profiles.ini')
    profiles = [v for k, v in config.items() if k.startswith('Profile')]
    try:
        if name:
            profile = next(p for p in profiles if p['name'] == name)
        else:
            profile = next(p for p in profiles if 'Default' in p and int(p['Default']))
    except StopIteration:
        raise ProfileNotFoundError(name or '(default)')
    profile_path = Path(profile['Path'])
    if int(profile['IsRelative']):
        return mozilla_dir / profile_path
    return profile_path


def feature_map():
    from firefed.feature import Feature
    return OrderedDict(
        sorted((m.__name__.lower(), m) for m in Feature.__subclasses__())
    )


def moz_datetime(ts):
    """Convert Mozilla timestamp to datetime."""
    return datetime.fromtimestamp(moz_timestamp(ts))


def moz_timestamp(ts):
    """Convert Mozilla timestamp to UNIX timestamp."""
    return ts // 1000000


def profile_dir_type(dirname):
    try:
        return profile_dir(dirname)
    except ProfileNotFoundError as e:
        raise argparse.ArgumentTypeError(e)


def make_parser():
    parser = argparse.ArgumentParser(
        'firefed',
        description=version.__description__,
    )
    parser.add_argument(
        '-p',
        '--profile',
        help='profile name or directory',
        type=profile_dir_type,
        default='',
    )
    parser.add_argument(
        '-s',
        '--summarize',
        action='store_true',
        help='summarize results',
    )
    subparsers = parser.add_subparsers(
        title='features',
        metavar='FEATURE',
        description='You must choose a feature.',
        dest='feature',
    )
    subparsers.required = True
    for name, Feature in feature_map().items():
        feature_parser = subparsers.add_parser(name, help=Feature.description)
        Feature.add_arguments(feature_parser)
    return parser
