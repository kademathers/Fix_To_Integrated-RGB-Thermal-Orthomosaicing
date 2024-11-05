import os
import io

import yaml
from appsettings.parser import SettingsParser
from argparse import ArgumentError

f = io.StringIO()
raw_cfg = yaml.safe_dump({'color': 'blue', 'timeout': 10})
if isinstance(raw_cfg, bytes):
    raw_cfg = raw_cfg.decode()
f.write(raw_cfg)


# Ensure that argparse still works.
def test_normal_arg():
    parser = SettingsParser()
    parser.add_argument('--blah')

    args = parser.parse_args(['--blah', 'hello'])

    assert args.blah == 'hello'

def test_normal_default():
    parser = SettingsParser()
    parser.add_argument('--blah', default='nope')

    args = parser.parse_args([])

    assert args.blah == 'nope'


def test_env_var():
    os.environ['FAVCOLOR'] = 'blue'
    parser = SettingsParser()
    parser.add_argument('--color', env_var='FAVCOLOR')
    args = parser.parse_args([])
    assert args.color == 'blue'


def test_yaml_value():
    f.seek(0)
    parser = SettingsParser(yaml_file=f)
    parser.add_argument('--color')
    args = parser.parse_args([])
    assert args.color == 'blue'

def test_nonexistant_yaml_value():
    f.seek(0)
    parser = SettingsParser(yaml_file=f)
    parser.add_argument('--color')
    args = parser.parse_args([])
    try:
        args.timeout
    except AttributeError:
        return

    raise Exception("Found non-defined value")

def test_yaml_type():
    f.seek(0)
    parser = SettingsParser(yaml_file=f)
    parser.add_argument('--timeout', type=int)
    args = parser.parse_args([])
    assert args.timeout == 10
    assert isinstance(args.timeout, int)


def test_yaml_incorrect_type():
    f.seek(0)
    parser = SettingsParser(yaml_file=f)
    parser.add_argument('--color', type=int)

    try:
        parser.parse_args([])
    except ArgumentError:
        return

    raise Exception("Read incorrect type")


def test_env_var_default_used():
    parser = SettingsParser()
    parser.add_argument('--color', env_var='FAVCOLOR', default='green')

    # Make sure there's not actually a FAVCOLOR env var
    if 'FAVCOLOR' in os.environ:
        os.environ.pop('FAVCOLOR')

    args = parser.parse_args([])
    assert args.color == 'green'


def test_add_setting():
    parser = SettingsParser()
    parser.add_setting('foo', 'bar')
    args = parser.parse_args([])
    assert args.foo == 'bar'
