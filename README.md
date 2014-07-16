# Charmguardian

A testing tool for Juju charms, bundles, and charm/bundle merge proposals.

## Installation

Clone repo and run `make` in the top-level directory.

## Usage

Activate the virtualenv: `source .venv/bin/activate`

Test a charm:

    charmguardian lp:~charmers/charms/precise/ghost/trunk > output.json

Test a bundle:

    charmguardian lp:~bac/charms/bundles/charmworld-demo/bundle > output.json

## Output

See the `examples/` directory for sample output.

## Notes

* Right now all testing is done using the local provider (see TODO)
* When testing a charm, if the charm is included in any bundles, the
  tests for those bundles will be run also, using the version of the
  charm under test.
* When testing a bundle, if multiple deployments are included in the
  bundle file, one is selected randomly and tests are run against that
  deployment. This may change or be configurable in the future.
* Right now only bzr lp:-style urls are supported (see TODO)

## TODO

There's still a lot to be done:

* Make testing environments configurable via environment vars.
* Add merge proposal testing.
* Add Fetchers for more url and repo types, e.g. http, git, etc
* Add support for testing at specific revisions (other than just HEAD)
* Add tests
