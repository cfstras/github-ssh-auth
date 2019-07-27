#!/bin/sh
"exec" "`dirname $0`/.env/bin/python" "$0" "$@"
import argparse
import base64
import difflib
import logging
import os
import shutil
import sys

import sshpubkeys
import yaml
from github import Github

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

UNCONFIGURED_TOKEN = "TOKEN"
CONFIG_PATH = SCRIPT_PATH + "/config.yml"
EXAMPLE_CONFIG_PATH = SCRIPT_PATH + "/config.example.yml"

logging.basicConfig(
    format="[%(levelname) 7s][%(module) 7s] %(message)s",
    level=logging.INFO)

LOG = logging.getLogger('main')


def main(args):
    options = get_options(args)

    config = get_config(options.config)
    if not config:
        LOG.error("Please edit %s to provide token.", options.config)
        return 1
    g = Github(config['token'])

    target = os.path.expanduser(config['target'])
    intermediate_target = target + ".new"

    org = config['organization']
    team = config.get('team')

    new_lines = generate_content(fallback=config.get('fallback_keys'), g=g, org=org, team=team)
    compare_existing(new_lines, target)
    if not options.no_action:
        write_output(intermediate_target, new_lines, target)
    else:
        LOG.warning("Exiting because --no-action was specified.")


def get_options(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug",
        help="debug output",
        action="store_true")
    parser.add_argument("-n", "--no-action",
        help="don't write any files, just fetch info and report differences",
        action="store_true")
    parser.add_argument("-c", "--config",
        help="path to configuration file. default: {}".format(CONFIG_PATH),
        default=CONFIG_PATH)
    options = parser.parse_args(args[1:])
    if options.debug:
        LOG.setLevel(logging.DEBUG)
    return options


def write_output(intermediate_target, new_lines, target):
    LOG.debug("Using temp file %s", intermediate_target)
    with open(intermediate_target, "w") as fd:
        fd.writelines(new_lines)
    os.rename(intermediate_target, target)
    LOG.info("File written to %s", target)


def compare_existing(new_lines, target):
    if os.path.exists(target):
        old_lines = open(target).readlines()
        diff = difflib.unified_diff(old_lines, new_lines, fromfile="old", tofile="new", n=1)
        joined = "".join(diff)
        if joined.strip():
            LOG.info("Differences:\n%s", joined)
        else:
            LOG.info("No differences.")
    else:
        LOG.warning("File %s does not exist, creating.", target)


def generate_content(fallback, g, org, team):
    new_lines = [l + "\n" for l in get_fallback(fallback)]
    lines = export_keys(g, org, team)
    new_lines.extend([l + "\n" for l in lines])
    return new_lines


def get_fallback(fallback):
    if not fallback:
        return
    yield "# fallback:"
    for line in fallback.strip().split("\n"):
        if line.startswith('#'):
            yield line
        else:
            line = validate_key(line)
            if line:
                yield line


def get_config(path):
    try:
        with open(path) as fd:
            config = yaml.safe_load(fd)
        if config['token'] == UNCONFIGURED_TOKEN:
            return None
        return config
    except FileNotFoundError:
        shutil.copy(EXAMPLE_CONFIG_PATH, path)
        return None


def export_keys(g, org, team):
    num_keys, num_users = 0, 0

    yield "### members from org {}, team {}".format(org, team)
    for member in sorted(get_members(org, team, g), key=lambda m:m.login):
        yield "# {}".format(member.login)
        num_member_keys = 0
        for key in sorted(member.get_keys(), key=lambda k:k.id):
            line = "{} {}\n".format(key.key, member.login)
            key = validate_key(line)
            if key:
                yield key
                num_keys += 1
                num_member_keys += 1
        LOG.debug("Member %s: %d keys", member.login, num_member_keys)
        yield ""
        num_users += 1
    yield ""
    LOG.info("Fetched %s keys from %s users in org %s %s",
        num_keys, num_users, org, team)


def validate_key(line):
    if not line:
        return None
    key = sshpubkeys.SSHKey(line, skip_option_parsing=True)
    try:
        key.parse()
        # rebuild the key to make sure it's safe
        raw_key = base64.b64encode(key._decoded_key).decode('UTF-8')
        return "{type:s} {key:s} {bits:d} {comment:s}".format(
            type=key.key_type.decode('UTF-8'),
            key=raw_key,
            bits=key.bits,
            comment=key.comment)
    except sshpubkeys.InvalidKeyError as err:
        LOG.warning("Skipping invalid key %s: %s", line, str(err))
    except NotImplementedError as err:
        LOG.warning("Skipping unknown key type: %s", str(err))
    return None


def get_members(org, team, g):
    LOG.info("Fetching org %s and team %s", org, team)
    group = g.get_organization(org)
    if team:
        group = group.get_team_by_slug(team)
    for member in group.get_members():
        yield member


if __name__ == "__main__":
    sys.exit(main(sys.argv))
