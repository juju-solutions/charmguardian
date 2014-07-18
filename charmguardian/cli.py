"""
charmguardian is a test-runner for Juju charms and bundles.
---
Use CHARM_TEST_ENVS and BUNDLE_TEST_ENVS to control which Juju environments
are used for tests (default is 'local').

Test results are written to stdout as json.


EXAMPLES

# Set test environments
export CHARM_TEST_ENVS=local,amazon
export BUNDLE_TEST_ENVS=local,amazon

# Test Launchpad repo at tip
charmguardian lp:~charmers/charms/precise/ghost/trunk

# Test Launchpad merge proposal (target branch must contain charm or bundle)
charmguardian lp:~davidpbritton/charms/precise/apache2/avoid-regen-cert/+merge/221102

# Test Github repo at specific revision
charmguardian gh:charms/apache2 52e73d

# Test local directory
charmguardian local:~/src/charms/precise/meteor

"""
import argparse
import json
import logging

from .testers import test

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def get_parser():
    description, epilog = __doc__.split('---')

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description,
        epilog=epilog,
    )

    parser.add_argument(
        'url',
        help='URL of the charm/bundle/merge proposal to test.',
    )
    parser.add_argument(
        'revision', nargs='?',
        help='Revision to test. Defaults to HEAD of branch implied by URL.',
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    result = test(args.url, args.revision)
    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
