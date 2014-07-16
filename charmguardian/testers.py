import logging
import os
import random
import re
import tempfile
import yaml

from charmworldlib.bundle import Bundles

from .fetchers import get_fetcher
from .util import (
    bundletester,
    get_charm_test_envs,
    get_bundle_test_envs,
    get_test_result,
    timestamp,
)

log = logging.getLogger(__name__)


class Tester(object):
    def __init__(self, url, revision, tempdir):
        self.url = url
        self.revision = revision
        self.tempdir = tempdir
        self.fetcher = get_fetcher(url, revision)


class BundleTester(Tester):
    @staticmethod
    def can_test(url):
        return '/charms/bundles/' in url

    def __init__(self, url, revision, tempdir):
        super(BundleTester, self).__init__(url, revision, tempdir)
        self.bundle_name = self._parse_url(url)
        self.bundledir = tempfile.mkdtemp(
            prefix='bundle-{}'.format(self.bundle_name), dir=tempdir)

    def _parse_url(self, url):
        m = re.search(r'/charms/bundles/([\w-]+)', url)
        return m.group(1)

    def test(self, charm_name=None, charmdir=None):
        start = timestamp()
        bundle_tests = {}
        result = 'pass'

        log.debug('Cloning Bundle %s to %s', self.bundle_name, self.bundledir)
        self.fetcher.fetch(self.bundledir)
        if charm_name and charmdir:
            self._swap_charm(charm_name, charmdir)

        for deployment in self._choose_deployments():
            bundle_tests[deployment] = deployment_tests = {}
            for env in get_bundle_test_envs():
                log.debug(
                    'Testing deployment %s in env %s', deployment, env)
                deployment_tests[env] = bundletester(
                    self.bundledir, env, deployment=deployment)
                if result == 'pass':
                    result = get_test_result(deployment_tests[env])

        return {
            'url': self.url,
            'revision': self.revision,
            'result': result,
            'started': start,
            'finished': timestamp(),
            'tests': bundle_tests,
        }

    def _swap_charm(self, charm_name, charmdir):
        bundle_file = os.path.join(self.bundledir, 'bundles.yaml')
        with open(bundle_file, 'r') as f:
            bundle_data = yaml.load(f)
        for bundle in bundle_data.itervalues():
            for svc in bundle['services'].itervalues():
                if charm_name in svc['charm']:
                    svc['branch'] = charmdir
                    del svc['charm']
        with open(bundle_file, 'w') as f:
            f.write(yaml.dump(bundle_data, default_flow_style=False))

    def _choose_deployments(self):
        bundle_file = os.path.join(self.bundledir, 'bundles.yaml')
        with open(bundle_file, 'r') as f:
            bundle_data = yaml.load(f)
            log.debug('Deployments: %s', bundle_data.keys())
            return [random.choice(bundle_data.keys())]


class CharmTester(Tester):
    @staticmethod
    def can_test(url):
        return '/charms/' in url

    def __init__(self, url, revision, tempdir):
        super(CharmTester, self).__init__(url, revision, tempdir)
        self.series, self.charm_name = self._parse_url(url)
        self.charmdir = os.path.join(tempdir, self.series, self.charm_name)
        os.makedirs(self.charmdir)

    def _parse_url(self, url):
        m = re.search(r'/charms/(\w+)/([\w-]+)', url)
        return m.group(1), m.group(2)

    def test(self):
        start = timestamp()
        charm_tests, bundle_tests = {}, {}
        result = 'pass'

        log.debug('Cloning Charm to %s', self.charmdir)
        self.fetcher.fetch(self.charmdir)
        for env in get_charm_test_envs():
            log.debug('Testing Charm %s in env %s', self.charm_name, env)
            charm_tests[env] = bundletester(self.charmdir, env)
            if result == 'pass':
                result = get_test_result(charm_tests[env])

        for bundle in self.bundles():
            bundle_tester = BundleTester(
                'lp:' + bundle.branch_spec, None, self.tempdir)
            bundle_tests[bundle.id] = bundle_tester.test(
                charm_name=self.charm_name, charmdir=self.charmdir)
            if result == 'pass':
                if bundle_tests[bundle.id]['result'] == 'fail':
                    result = 'fail'

        return {
            'url': self.url,
            'revision': self.revision,
            'result': result,
            'started': start,
            'finished': timestamp(),
            'tests': {
                'charm': charm_tests,
                'bundle': bundle_tests,
            }
        }

    def bundles(self):
        bundles = [bundle for bundle in Bundles().search(self.charm_name)
                   if self.charm_name in bundle.charms]
        log.debug(
            'Bundles that contain %s: %s', self.charm_name,
            ', '.join([b.basket_name for b in bundles]))
        return bundles


TESTERS = [
    #MergeProposalTester,
    BundleTester,
    CharmTester,
]


def get_tester(url, revision, tempdir):
    for tester in TESTERS:
        if tester.can_test(url):
            return tester(url, revision, tempdir)
    raise ValueError('No tester for url: %s' % url)
