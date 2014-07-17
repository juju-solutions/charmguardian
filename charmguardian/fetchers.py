import logging
import shlex
import subprocess
import tempfile

import requests

log = logging.getLogger(__name__)


class Fetcher(object):
    def __init__(self, url, revision):
        self.url = url
        self.revision = revision


class BzrFetcher(Fetcher):
    @staticmethod
    def can_fetch(url):
        return url.startswith('lp:') and '/+merge/' not in url

    def fetch(self, dir_):
        dir_ = tempfile.mkdtemp(dir=dir_)
        log.debug('Cloning %s to %s', self.url, dir_)
        bzr('branch --use-existing-dir {} {}'.format(self.url, dir_))
        # TODO checkout correct revision
        return dir_


class BzrMergeProposalFetcher(Fetcher):
    @staticmethod
    def can_fetch(url):
        return url.startswith('lp:') and '/+merge/' in url

    def fetch(self, dir_):
        dir_ = tempfile.mkdtemp(dir=dir_)
        api_base = 'https://api.launchpad.net/devel/'
        url = api_base + self.url[len('lp:'):]
        merge_data = requests.get(url).json()
        target = 'lp:' + merge_data['target_branch_link'][len(api_base):]
        source = 'lp:' + merge_data['source_branch_link'][len(api_base):]
        log.debug('Cloning %s to %s', target, dir_)
        bzr('branch --use-existing-dir {} {}'.format(target, dir_))
        log.debug('Merging %s into %s', source, dir_)
        bzr('merge {}'.format(source), cwd=dir_)
        return dir_


def bzr(cmd, **kw):
    cmd = 'bzr ' + cmd
    args = shlex.split(cmd)
    subprocess.check_call(args, **kw)


FETCHERS = [
    BzrFetcher,
    BzrMergeProposalFetcher,
    # GitFetcher,
]


def get_fetcher(url, revision):
    if url.startswith('~'):
        url = 'lp:' + url

    for fetcher in FETCHERS:
        if fetcher.can_fetch(url):
            return fetcher(url, revision)
    raise ValueError('No fetcher for url: %s' % url)
