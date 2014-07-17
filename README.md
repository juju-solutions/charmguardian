# Charmguardian

A testing tool for Juju charms, bundles, and charm/bundle merge proposals.

## Installation

Clone repo and run `make` in the top-level directory.

## Usage

Activate the virtualenv: `source .venv/bin/activate`

Test a charm:

    CHARM_TEST_ENVS=local,amazon charmguardian lp:~charmers/charms/precise/ghost/trunk > output.json

Test a bundle:

    BUNDLE_TEST_ENVS=local,amazon charmguardian lp:~bac/charms/bundles/charmworld-demo/bundle > output.json

Test a merge proposal (target branch must contain a charm or bundle):

    charmguardian lp:~davidpbritton/charms/precise/apache2/avoid-regen-cert/+merge/221102

If `CHARM_TEST_ENVS` or `BUNDLE_TEST_ENVS` are not set, the `local`
environment is used for all tests.

## Output

See the `examples/` directory for sample output.

## Notes

* When testing a charm, if the charm is included in any bundles, the
  tests for those bundles will be run also, using the version of the
  charm under test.
* When testing a bundle, if multiple deployments are included in the
  bundle file, one is selected randomly and tests are run against that
  deployment. This may change or be configurable in the future.
* Right now only bzr lp:-style urls are supported (see TODO)

## TODO

There's still a lot to be done:

* Add Fetchers for more url and repo types, e.g. http, git, etc
* Add support for testing at specific revisions (other than just HEAD)
* Add tests
