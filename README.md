# Charmguardian

A testing tool for Juju charms, bundles, and charm/bundle merge proposals.

## Installation

Clone repo and run `make` in the top-level directory.

## Usage

First activate the virtualenv: `source .venv/bin/activate`

```
$ charmguardian -h
usage: charmguardian [-h] [--debug] [--shallow] [--workspace WORKSPACE]
                     url [revision]

charmguardian is a test-runner for Juju charms and bundles.

positional arguments:
  url                   URL of the charm/bundle/merge proposal to test.
  revision              Revision to test. Defaults to HEAD of branch implied
                        by URL.

optional arguments:
  -h, --help            show this help message and exit
  --debug               Increase output verbosity and skip cleanup of temp
                        files.
  --shallow             When testing a charm, test the charm only; do not test
                        bundles which contain the charm.
  --workspace WORKSPACE
                        Directory in which to write temp files. If not
                        specified, temp files will be written to the platform
                        default location and deleted upon process termination.

Use CHARM_TEST_ENVS and BUNDLE_TEST_ENVS to control which Juju
environments
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
```

## Output

See the `examples/` directory for sample output.

## Notes

* When testing a charm, if the charm is included in any bundles, the
  tests for those bundles will be run also, using the version of the
  charm under test.
* When testing a bundle, if multiple deployments are included in the
  bundle file, one is selected randomly and tests are run against that
  deployment. This may change or be configurable in the future.
