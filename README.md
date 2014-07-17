# Charmguardian

A testing tool for Juju charms, bundles, and charm/bundle merge proposals.

## Installation

Clone repo and run `make` in the top-level directory.

## Usage

* Activate the virtualenv: `source .venv/bin/activate`
* Run `charmguardian URL`, where URL is the path to the local or remote
  charm or bundle to test (see Examples below).
* Use `CHARM_TEST_ENVS` and `BUNDLE_TEST_ENVS` to specify which juju
  environments are used for tests (default is 'local').
* Test results are written to stdout as json.

## Examples

### Launchpad

Test a charm using the default 'local' environment:

    charmguardian lp:~charmers/charms/precise/ghost/trunk

Test a bundle using the 'local' and 'amazon' environments:

    BUNDLE_TEST_ENVS=local,amazon charmguardian lp:~bac/charms/bundles/charmworld-demo/bundle

Test a merge proposal (target branch must contain a charm or bundle):

    charmguardian lp:~davidpbritton/charms/precise/apache2/avoid-regen-cert/+merge/221102

### Github

Test a charm, redirecting json results to a file:

    charmguardian gh:tvansteenburgh/meteor-charm > test_results.json

### Local Filesystem

Test a charm:

    charmguardian local:~/src/charms/precise/meteor

## Output

See the `examples/` directory for sample output.

## Notes

* When testing a charm, if the charm is included in any bundles, the
  tests for those bundles will be run also, using the version of the
  charm under test.
* When testing a bundle, if multiple deployments are included in the
  bundle file, one is selected randomly and tests are run against that
  deployment. This may change or be configurable in the future.

## TODO

There's still a lot to be done:

* Add Fetchers for more url and repo types
* Add support for testing at specific revisions (other than just HEAD)
* Add tests
