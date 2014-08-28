import json
import os
import shutil
import tempfile
import unittest

import mock

from ..testers import (
    BundleTester,
    CharmTester,
)


class BundleTesterTest(unittest.TestCase):
    @mock.patch('charmguardian.testers.bundletester')
    def test_test(self, bundletester):
        bundletester.return_value = {}
        bundletester.__class__ = mock.MagicMock

        tempdir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(tempdir))
        t = BundleTester(tempdir)
        t._choose_deployments = lambda: ['deployment1']

        result = t.test()
        expected = {
            'type': 'bundle',
            'result': 'pass',
            'tests': {
                'deployment1': {
                    'local': {

                    }
                }
            }
        }
        self.assertEqual(expected, result)


class CharmTesterTest(unittest.TestCase):
    @mock.patch('charmguardian.testers.bundletester')
    def test_test(self, bundletester):
        bundletester.return_value = {}
        bundletester.__class__ = mock.MagicMock

        tempdir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(tempdir))
        with open(os.path.join(tempdir, 'metadata.yaml'), 'w') as f:
            json.dump(dict(name=os.path.basename(tempdir)), f)
        t = CharmTester(tempdir)
        t.bundles = lambda: []

        result = t.test()
        expected = {
            'type': 'charm',
            'result': 'pass',
            'tests': {
                'charm': {
                    'local': {

                    }
                },
                'bundle': {},
            }
        }
        self.assertEqual(expected, result)
