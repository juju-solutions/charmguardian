"""
A tool for reporting on charmguardian test results.
---
Test results are downloaded from http://reports.vapour.ws/charm-tests-by-charm
and cached locally in ~/.charmguardian-report-cache. New results, if present,
are added to the local cache each time the program runs.

Simple Usage
============

Running the program with no args will print a list of all charms for which
test results are available.

Running the program with one argument (a charm url) will print the test results
for that charm.

Filtering Results
=================

Each test result contains a number of fields against which we can apply
filters.  An example test result:

    {
      executable: [
        "/var/lib/jenkins/charmguardian/.venv/bin/charm-proof"
      ],
      returncode: 0,
      duration: 0.690053,
      suite: "apache2",
      test: "charm-proof",
      output: "I: relation logging has no hooks ",
      dirname: "/var/lib/jenkins/workspace/charm-bundle-test/tmpF8jImE/apache2"
    }

To filter, run with a yaml file containing the desired filtering expressions.
An example yaml file:

    $ cat filter.yaml
    returncode: content != 0
    test: content not in ('charm-proof', 'make lint')
    output: not content.startswith('bundletester failed')

A filter is named to match the test result field to which it is applied.
String filters are evaluated by python and are supplied a `content` variable
containing the value from the test result. Python's `re` module is also
available in the global namespace in which the expression will be evaulated.

The filtering expressions are ANDed together, therefore all expressions must
evaulate true for the test result to match the filter.

The value of the filter can be alternatively be an int or boolean.

    - int:  return (test result value == filter value)
    - bool: return the value of the expression

The default filtering mode will return a test result if *any* of its tests
match the filter. To return a result only if *all* tests match the filter,
pass the `--all` option.

"""
import argparse
import logging
import json
import os
import re
import requests
import sys
import yaml

from datetime import datetime

from BeautifulSoup import BeautifulSoup

REPORT_HOME = "http://reports.vapour.ws/charm-tests-by-charm"
CACHE = '~/.charmguardian-report-cache'
DATE_FORMAT = "%B %d %Y at %H:%M:%S"
log = logging.getLogger(__name__)


class Result(object):
    def __init__(self, name, date, url, results=None):
        self.name = name
        self.date = date
        self.url = url
        self.results = results or {}

    @classmethod
    def from_cache(cls, data):
        obj = cls(
            data.pop('name'),
            data.pop('date'),
            data.pop('url'),
            data.pop('results'),
        )
        for k, v in data.items():
            setattr(obj, k, v)
        return obj

    def set_status_from_row(self, row):
        states = row.findAll('td')[2:]
        self.all_passing = all([x.text.upper() == 'PASS' for x in states])
        self.all_failing = all([x.text.upper() == 'FAIL' for x in states])

    @property
    def datetime(self):
        return datetime.strptime(self.date, DATE_FORMAT)

    def fetch_results(self):
        self.results = requests.get(self.url + '/json').json()

    def to_json(self):
        return self.__dict__

    @property
    def tests(self):
        for test in self._get_tests(self.results):
            yield test

    def _get_tests(self, d):
        if 'returncode' in d:
            yield d

        for k, v in d.items():
            if isinstance(v, dict):
                for item in self._get_tests(v):
                    yield item
            if isinstance(v, list):
                for listitem in v:
                    if isinstance(listitem, dict):
                        for dictitem in self._get_tests(listitem):
                            yield dictitem


class Query(object):
    def __init__(self, cfg, args):
        self.cfg = cfg
        self.args = args

    def find(self, items):
        for item in items:
            if self.match(item.tests):
                yield item

    def match(self, tests):
        matches = []
        for test in tests:
            for filter_ in self.cfg:
                if not self.match_filter(filter_, test):
                    matches.append(False)
                    break
            else:
                matches.append(True)
                if self.args.any:
                    return True
        return all(matches)

    def match_filter(self, filter_, test):
        if filter_ not in test:
            return True

        expression = self.cfg[filter_]
        content = test.get(filter_)
        if isinstance(expression, bool):
            return expression
        if isinstance(expression, int):
            return expression == content
        if isinstance(expression, basestring):
            res = eval(expression, dict(re=re), dict(content=content))
            return res


def report(args):
    html = requests.get(REPORT_HOME).text
    soup = BeautifulSoup(html)
    results = {}
    for r in soup.findAll('tr')[1:]:
        tds = r.findAll('td')
        name = tds[0].text
        date = tds[1].text
        url = tds[1].find('a')['href']
        results[name] = Result(name, date, url)
        results[name].set_status_from_row(r)

    cached_results = {}
    cache_file = os.path.expanduser(CACHE)
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cached_results = {
                k: Result.from_cache(v) for k, v in json.load(f).items()}

    for r in results.values():
        cached = cached_results.get(r.name)
        if not cached or cached.datetime < r.datetime:
            log.debug('Updating cache for %s', r.name)
            r.fetch_results()
            cached_results[r.name] = r

    log.debug('Writing cache file')
    with open(cache_file, 'w') as f:
        json.dump({k: v.to_json() for k, v in cached_results.items()}, f)

    if args.test_result_url:
        if args.test_result_url not in cached_results:
            sys.stderr.write(
                'No test results found for ' + args.test_result_url)
            sys.exit(1)
        else:
            print json.dumps(
                cached_results[args.test_result_url].results, indent=2)
            sys.exit(0)

    if not args.filter:
        cfg = {'returncode': True}
    else:
        cfg = yaml.load(open(args.filter))
    query = Query(cfg, args)
    query_results = query.find(cached_results.values())
    for r in query_results:
        print r.name


def get_parser():
    description, epilog = __doc__.split('---')

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description,
        epilog=epilog,
    )

    parser.add_argument(
        'test_result_url', nargs='?',
        help='A charm test url, e.g. cs:precise/pictor-4. If supplied, '
             'prints test result details for the charm (as json). '
    )
    parser.add_argument(
        '-f', '--filter',
        help='YAML file containing filter to apply to test results. '
             'The default filter matches all test results. '
    )
    parser.add_argument(
        '--any', action='store_true',
        help='Return charms for which any test result matches the filter.',
    )
    parser.add_argument(
        '--all', action='store_true',
        help='Return charms for which all test results match the filter.',
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Show debug output',
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.ERROR,
        format='%(asctime)s %(message)s',
    )

    if not (args.any or args.all):
        args.any = True

    report(args)


if __name__ == '__main__':
    main()
