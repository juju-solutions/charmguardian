import shlex
import subprocess


class Fetcher(object):
    def __init__(self, url, revision):
        self.url = url
        self.revision = revision


class BzrFetcher(Fetcher):
    @staticmethod
    def can_fetch(url):
        return url.startswith('lp:')

    def fetch(self, dir_):
        cmd = 'bzr branch --use-existing-dir {} {}'.format(self.url, dir_)
        args = shlex.split(cmd)
        subprocess.check_call(args)
        #TODO checkout correct revision


FETCHERS = [
    BzrFetcher,
    #GitFetcher,
]


def get_fetcher(url, revision):
    for fetcher in FETCHERS:
        if fetcher.can_fetch(url):
            return fetcher(url, revision)
    raise ValueError('No fetcher for url: %s' % url)
