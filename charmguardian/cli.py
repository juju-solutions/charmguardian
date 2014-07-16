import argparse
import json
import logging
import tempfile

from .testers import get_tester

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def test(url, revision):
    tempdir = tempfile.mkdtemp()
    tester = get_tester(url, revision, tempdir)
    result = tester.test()
    return result


def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'url',
        help='URL of the charm/bundle/merge proposal to test.',
    )
    parser.add_argument(
        'revision', nargs='?',
        help='Revision to test. Defaults to HEAD of branch implied by URL.',
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    result = test(args.url, args.revision)
    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
