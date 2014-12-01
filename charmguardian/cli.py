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

# Test charm from Charm Store
charmguardian cs:wordpress
charmguardian cs:precise/wordpress

# Test bundle from Store
charmguardian bundle:mediawiki/single
charmguardian bundle:mediawiki/6/single
charmguardian bundle:~charmers/mediawiki/single
charmguardian bundle:~charmers/mediawiki/6/single

# Test Launchpad repo at tip
charmguardian lp:~charmers/charms/precise/ghost/trunk
charmguardian launchpad:~charmers/charms/precise/ghost/trunk
charmguardian https://launchpad.net/~charmers/charms/precise/ghost/trunk

# Test Launchpad merge proposal (target branch must contain charm or bundle)
charmguardian\
 lp:~davidpbritton/charms/precise/apache2/avoid-regen-cert/+merge/221102

# Test Github repo at specific revision
charmguardian gh:charms/apache2 52e73d
charmguardian github:charms/apache2 52e73d
charmguardian https://github.com/charms/apache2 52e73d

# Test Bitbucket repo at specific revision
# (For Bitbucket, repos that don't end in '.git' are assumed to be Mercurial.)
charmguardian bb:battlemidget/juju-apache-gunicorn-django.git
charmguardian bitbucket:battlemidget/juju-apache-gunicorn-django.git
charmguardian\
 https://bitbucket.org/battlemidget/juju-apache-gunicorn-django.git

# Test local directory
charmguardian local:~/src/charms/precise/meteor

"""
import argparse
import json
import logging
import os
import sys

from .testers import test
from .formatters import fmt


class validate_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        path = os.path.abspath(os.path.expanduser(values))
        if not os.path.isdir(path):
            sys.stderr.write(
                "Invalid workspace directory: {}\n".format(values))
            sys.exit(2)
        setattr(namespace, self.dest, path)


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
        '--constraints',
        help='Passed to `juju bootstrap`',
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Increase output verbosity and skip cleanup of temp files.',
    )
    parser.add_argument(
        '--shallow', action='store_true',
        help='When testing a charm, test the charm only; do not test bundles '
             'which contain the charm.',
    )
    parser.add_argument(
        '--workspace', action=validate_dir, default=None,
        help='Directory in which to write temp files. If not specified, temp '
             'files will be written to the platform default location and '
             'deleted upon process termination.',
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.ERROR,
        format='%(asctime)s %(message)s',
    )

    try:
        result = test(
            args.url,
            revision=args.revision,
            shallow=args.shallow,
            workspace=args.workspace,
            constraints=args.constraints,
        )
        result = fmt(args.url, result)
        print(json.dumps(result, indent=4))
        sys.stderr.write(
            '\nTest result: {}\n'.format(result['result'].upper()))
    except Exception as e:
        sys.stderr.write('{}\n'.format(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
