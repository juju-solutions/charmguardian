from contextlib import contextmanager
import logging
import multiprocessing
import os
import random
import shutil
import signal
import tempfile
import yaml

from amulet.helpers import setup_bzr, run_bzr
from charmworldlib.bundle import Bundles

from .fetchers import (
    get_fetcher,
    FetchError,
)
from .util import (
    bundletester,
    get_charm_test_envs,
    get_bundle_test_envs,
    get_test_result,
    timestamp,
)

log = logging.getLogger(__name__)


def init_worker():
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)


@contextmanager
def signal_handlers(pool):
    def install_handler(signum):
        cur_handler = signal.getsignal(signum)

        def handler(signum, frame):
            pool.terminate()
            pool.join()
            if callable(cur_handler):
                cur_handler(signum, frame)
        signal.signal(signum, handler)
        return cur_handler

    prev_sigint_handler = install_handler(signal.SIGINT)
    prev_sigterm_handler = install_handler(signal.SIGTERM)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, prev_sigint_handler)
        signal.signal(signal.SIGTERM, prev_sigterm_handler)


class Tester(object):
    def __init__(self, test_dir):
        self.test_dir = test_dir


class BundleTester(Tester):
    @staticmethod
    def can_test(dir_):
        return 'bundles.yaml' in os.listdir(dir_)

    def test(self, shallow=False, workspace=None, constraints=None,
             charm_name=None, charmdir=None):
        bundle_tests = {}
        result = 'pass'
        exclude = None

        if charm_name and charmdir:
            self._ensure_bzr(charmdir)
            self._swap_charm(charm_name, charmdir)
            exclude = charm_name

        for deployment in self._choose_deployments():
            envs = get_bundle_test_envs()
            bundle_tests[deployment] = self._multi_test(
                envs, deployment, exclude, constraints)
            for env in envs:
                if result != 'pass':
                    break
                result = get_test_result(bundle_tests[deployment][env])

        return {
            'type': 'bundle',
            'result': result,
            'tests': bundle_tests,
        }

    def _multi_test(self, envs, deployment, exclude, constraints):
        results = {}
        pool = multiprocessing.Pool(None, init_worker)
        with signal_handlers(pool):
            for env in envs:
                log.debug(
                    'Testing deployment %s in env %s', deployment, env)
                results[env] = pool.apply_async(
                    bundletester,
                    (self.test_dir, env),
                    dict(
                        deployment=deployment,
                        exclude=exclude,
                        skip_implicit=True,
                        constraints=constraints,
                    )
                )

            for env, result in results.items():
                results[env] = result.get()

        return results

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

    def _multi_test(self, envs, constraints):
        results = {}
        pool = multiprocessing.Pool(None, init_worker)
        with signal_handlers(pool):
            for env in envs:
                log.debug('Testing Charm %s in env %s', self.charm_name, env)
                results[env] = pool.apply_async(
                    bundletester,
                    (self.test_dir, env),
                    dict(
                        constraints=constraints,
                    )
                )

            for env, result in results.items():
                results[env] = result.get()

        return results

    def test(self, shallow=False, workspace=None, constraints=None):
        charm_tests, bundle_tests = {}, {}
        result = 'pass'

        # to avoid charm-proof warnings, dir name must match charm name
        if os.path.basename(self.test_dir.rstrip('/')) != self.charm_name:
            new_test_dir = os.path.join(self.test_dir, self.charm_name)
            shutil.copytree(self.test_dir, new_test_dir, symlinks=True)
            self.test_dir = new_test_dir

        envs = get_charm_test_envs()
        charm_tests = self._multi_test(envs, constraints)
        for env in envs:
            if result != 'pass':
                break
            result = get_test_result(charm_tests[env])

        if not shallow:
            for bundle in self.bundles():
                log.debug('Testing bundle %s', bundle.id)
                bundle_tests[bundle.id] = test(
                    'lp:' + bundle.branch_spec,
                    workspace=workspace,
                    constraints=constraints,
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


def test(url, revision=None, shallow=False, workspace=None,
         constraints=None, **kw):
    tempdir = None
    try:
        tempdir = workspace or tempfile.mkdtemp()
        fetcher = get_fetcher(url, revision)
        try:
            test_dir = fetcher.fetch(tempdir)
        except FetchError as e:
            return {
                'type': 'error',
                'error': str(e),
                'result': 'fail',
                'url': url,
                'finished': timestamp(),
            }
        tester = get_tester(test_dir)

        start = timestamp()
        result = tester.test(
            shallow=shallow,
            workspace=workspace,
            constraints=constraints,
            **kw
        )
        stop = timestamp()

        result['url'] = url
        result['revision'] = fetcher.get_revision(test_dir)
        result['started'] = start
        result['finished'] = stop
    finally:
        if tempdir and not workspace:
            shutil.rmtree(tempdir)

    return result
