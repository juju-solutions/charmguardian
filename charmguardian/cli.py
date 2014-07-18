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
charmguardian launchpad:~charmers/charms/precise/ghost/trunk
charmguardian https://launchpad.net/~charmers/charms/precise/ghost/trunk

# Test Launchpad merge proposal (target branch must contain charm or bundle)
charmguardian lp:~davidpbritton/charms/precise/apache2/avoid-regen-cert/+merge/221102

# Test Github repo at specific revision
charmguardian gh:charms/apache2 52e73d
charmguardian github:charms/apache2 52e73d
charmguardian https://github.com/charms/apache2 52e73d

# Test Bitbucket repo at specific revision
# (For Bitbucket, repos that don't end in '.git' are assumed to be Mercurial.)
charmguardian bb:battlemidget/juju-apache-gunicorn-django.git
charmguardian bitbucket:battlemidget/juju-apache-gunicorn-django.git
charmguardian https://bitbucket.org/battlemidget/juju-apache-gunicorn-django.git

# Test local directory
charmguardian local:~/src/charms/precise/meteor

"""
import argparse
import json
import logging

from .testers import test


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
    parser.add_argument(
        '--debug', action='store_true',
        help='Increase output verbosity and skip cleanup of temp files.',
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.ERROR)

    result = test(args.url, revision=args.revision)
    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
