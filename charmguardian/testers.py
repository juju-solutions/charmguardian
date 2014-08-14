import logging
import os
import random
import shutil
import tempfile
import yaml

from amulet.helpers import setup_bzr, run_bzr
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
    def __init__(self, test_dir):
        self.test_dir = test_dir


class BundleTester(Tester):
    @staticmethod
    def can_test(dir_):
        return 'bundles.yaml' in os.listdir(dir_)

    def test(self, shallow=False, workspace=None, charm_name=None,
             charmdir=None):
        bundle_tests = {}
        result = 'pass'
        exclude = None

        if charm_name and charmdir:
            self._ensure_bzr(charmdir)
            self._swap_charm(charm_name, charmdir)
            exclude = charm_name

        for deployment in self._choose_deployments():
            bundle_tests[deployment] = deployment_tests = {}
            for env in get_bundle_test_envs():
                log.debug(
                    'Testing deployment %s in env %s', deployment, env)
                deployment_tests[env] = bundletester(
                    self.test_dir, env, deployment=deployment,
                    exclude=exclude, skip_implicit=True)
                if result == 'pass':
                    result = get_test_result(deployment_tests[env])

        return {
            'type': 'bundle',
            'result': result,
            'tests': bundle_tests,
        }

    def _ensure_bzr(self, charmdir):
        if os.path.exists(os.path.join(charmdir, '.bzr')):
            return

        setup_bzr(charmdir)
        run_bzr(["add", "."], charmdir)
        run_bzr([
            "commit", "--unchanged", "-m",
            "Creating local branch for deployer"],
            charmdir)

    def _swap_charm(self, charm_name, charmdir):
        bundle_file = os.path.join(self.test_dir, 'bundles.yaml')
        with open(bundle_file, 'r') as f:
            bundle_data = yaml.load(f)
        for bundle in bundle_data.itervalues():
            for svc in bundle['services'].itervalues():
                # TODO make this comparison more precise
                if charm_name in svc.get('charm', {}):
                    svc['branch'] = charmdir
                    del svc['charm']
        with open(bundle_file, 'w') as f:
            f.write(yaml.dump(bundle_data, default_flow_style=False))

    def _choose_deployments(self):
        bundle_file = os.path.join(self.test_dir, 'bundles.yaml')
        with open(bundle_file, 'r') as f:
            bundle_data = yaml.load(f)
            log.debug('Deployments: %s', bundle_data.keys())
            return [random.choice(bundle_data.keys())]


class CharmTester(Tester):
    @staticmethod
    def can_test(dir_):
        return 'metadata.yaml' in os.listdir(dir_)

    def __init__(self, test_dir):
        super(CharmTester, self).__init__(test_dir)
        self.charm_name = self._get_charm_name()

    def _get_charm_name(self):
        metadata_file = os.path.join(self.test_dir, 'metadata.yaml')
        with open(metadata_file, 'r') as f:
            metadata = yaml.load(f)
            return metadata['name']

    def test(self, shallow=False, workspace=None):
        charm_tests, bundle_tests = {}, {}
        result = 'pass'

        # to avoid charm-proof warnings, dir name must match charm name
        if os.path.basename(self.test_dir.rstrip('/')) != self.charm_name:
            new_test_dir = os.path.join(self.test_dir, self.charm_name)
            shutil.copytree(self.test_dir, new_test_dir)
            self.test_dir = new_test_dir

        for env in get_charm_test_envs():
            log.debug('Testing Charm %s in env %s', self.charm_name, env)
            charm_tests[env] = bundletester(self.test_dir, env)
            if result == 'pass':
                result = get_test_result(charm_tests[env])

        if not shallow:
            for bundle in self.bundles():
                log.debug('Testing bundle %s', bundle.id)
                bundle_tests[bundle.id] = test(
                    'lp:' + bundle.branch_spec,
                    workspace=workspace,
                    charm_name=self.charm_name,
                    charmdir=self.test_dir)
                if result == 'pass':
                    if bundle_tests[bundle.id]['result'] == 'fail':
                        result = 'fail'

        return {
            'type': 'charm',
            'result': result,
            'tests': {
                'charm': charm_tests,
                'bundle': bundle_tests,
            }
        }

    def bundles(self):
        bundles = [bundle for bundle in Bundles().search(self.charm_name)
                   if bundle.promulgated and self.charm_name in bundle.charms]
        log.debug(
            'Promulgated bundles that contain %s: %s', self.charm_name,
            ', '.join(['{}/{}'.format(b.basket_name, b.name) for b in bundles])
            if bundles else 'None')
        return bundles


TESTERS = [
    BundleTester,
    CharmTester,
]


def get_tester(test_dir):
    for tester in TESTERS:
        if tester.can_test(test_dir):
            return tester(test_dir)
    raise ValueError('No tester for dir: %s' % test_dir)


def test(url, revision=None, shallow=False, workspace=None, **kw):
    tempdir = None
    try:
        tempdir = workspace or tempfile.mkdtemp()
        fetcher = get_fetcher(url, revision)
        test_dir = fetcher.fetch(tempdir)
        tester = get_tester(test_dir)

        start = timestamp()
        result = tester.test(shallow=shallow, workspace=workspace, **kw)
        stop = timestamp()

        result['url'] = url
        result['revision'] = fetcher.get_revision(test_dir)
        result['started'] = start
        result['finished'] = stop
    finally:
        if tempdir and not workspace:
            shutil.rmtree(tempdir)

    return result
