import unittest

from ..formatters import (
    BundleFormatter,
    CharmFormatter,
)


class BundleFormatterTest(unittest.TestCase):
    def test_fmt(self):
        f = BundleFormatter().fmt
        result = {
            'tests': {},
            'result': 'pass',
            'revision': '1',
            'started': 'start',
            'finished': 'finish',
        }
        formatted = f('myurl', result)
        expected = {
            'tests': {
                'charm': {},
                'bundle': {
                    'myurl': {
                        'url': 'myurl',
                        'tests': {},
                        'result': 'pass',
                        'revision': '1',
                        'started': 'start',
                        'finished': 'finish',
                    }
                }
            },
            'result': 'pass',
            'revision': '1',
            'started': 'start',
            'finished': 'finish',
        }
        self.assertEqual(formatted, expected)


class CharmFormatterTest(unittest.TestCase):
    def test_fmt(self):
        f = CharmFormatter().fmt
        result = {
            'tests': {
                'bundle': {
                    'bundle1': {
                        'type': 'bundle',
                    },
                    'bundle2': {
                        'type': 'bundle',
                    },
                }
            }
        }
        formatted = f('myurl', result)
        expected = {
            'tests': {
                'bundle': {
                    'bundle1': {},
                    'bundle2': {},
                }
            }
        }
        self.assertEqual(formatted, expected)
