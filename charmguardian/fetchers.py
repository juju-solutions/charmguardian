import logging
import os
import re
import shlex
import shutil
import subprocess
import tempfile

import requests

log = logging.getLogger(__name__)


class Fetcher(object):
    def __init__(self, url, revision, **kw):
        self.url = url
        self.revision = revision
        for k, v in kw.items():
            setattr(self, k, v)

    @classmethod
    def can_fetch(cls, url):
        match = cls.MATCH.search(url)
        return match.groupdict() if match else {}

    def get_revision(self, dir_):
        return self.revision


class BzrFetcher(Fetcher):
    MATCH = re.compile(r"""
    ^(lp:|launchpad:|https?://((code|www)\.)?launchpad.net/)(?P<repo>.*)$
    """, re.VERBOSE)

    @classmethod
    def can_fetch(cls, url):
        matchdict = super(BzrFetcher, cls).can_fetch(url)
        return matchdict if '/+merge/' not in matchdict.get('repo', '') else {}

    def fetch(self, dir_):
        dir_ = tempfile.mkdtemp(dir=dir_)
        url = 'lp:' + self.repo
        cmd = 'branch --use-existing-dir {} {}'.format(url, dir_)
        if self.revision:
            cmd = '{} -r {}'.format(cmd, self.revision)
        bzr(cmd)
        return dir_

    def get_revision(self, dir_):
        rev_info = check_output('bzr revision-info', cwd=dir_)
        return rev_info.split()[1]


class BzrMergeProposalFetcher(BzrFetcher):
    @classmethod
    def can_fetch(cls, url):
        matchdict = super(BzrFetcher, cls).can_fetch(url)
        return matchdict if '/+merge/' in matchdict.get('repo', '') else {}

    def fetch(self, dir_):
        dir_ = tempfile.mkdtemp(dir=dir_)
        api_base = 'https://api.launchpad.net/devel/'
        url = api_base + self.repo
        merge_data = requests.get(url).json()
        target = 'lp:' + merge_data['target_branch_link'][len(api_base):]
        source = 'lp:' + merge_data['source_branch_link'][len(api_base):]
        bzr('branch --use-existing-dir {} {}'.format(target, dir_))
        bzr('merge {}'.format(source), cwd=dir_)
        return dir_


class GithubFetcher(Fetcher):
    MATCH = re.compile(r"""
    ^(gh:|github:|https?://(www\.)?github.com/)(?P<repo>.*)$
    """, re.VERBOSE)

    def fetch(self, dir_):
        dir_ = tempfile.mkdtemp(dir=dir_)
        url = 'https://github.com/' + self.repo
        git('clone {} {}'.format(url, dir_))
        if self.revision:
            git('checkout {}'.format(self.revision), cwd=dir_)
        return dir_

    def get_revision(self, dir_):
        return check_output('git rev-parse HEAD', cwd=dir_)


class BitbucketFetcher(Fetcher):
    MATCH = re.compile(r"""
    ^(bb:|bitbucket:|https?://(www\.)?bitbucket.org/)(?P<repo>.*)$
    """, re.VERBOSE)

    def fetch(self, dir_):
        dir_ = tempfile.mkdtemp(dir=dir_)
        url = 'https://bitbucket.org/' + self.repo
        if url.endswith('.git'):
            return self._fetch_git(url, dir_)
        return self._fetch_hg(url, dir_)

    def _fetch_git(self, url, dir_):
        git('clone {} {}'.format(url, dir_))
        if self.revision:
            git('checkout {}'.format(self.revision), cwd=dir_)
        return dir_

    def _fetch_hg(self, url, dir_):
        cmd = 'clone {} {}'.format(url, dir_)
        if self.revision:
            cmd = '{} -u {}'.format(cmd, self.revision)
        hg(cmd)
        return dir_

    def get_revision(self, dir_):
        cmd = "hg log -l 1 --template '{node}\n' -r ."
        if '.git' in os.listdir(dir_):
            cmd = 'git rev-parse HEAD'
        return check_output(cmd, cwd=dir_)


class LocalFetcher(Fetcher):
    MATCH = re.compile(r"""
    ^local:(?P<path>.*)$
    """, re.VERBOSE)

    def fetch(self, dir_):
        src = os.path.expanduser(self.path)
        dst = os.path.join(dir_, os.path.basename(src.rstrip('/')))
        shutil.copytree(src, dst)
        return dst


def bzr(cmd, **kw):
    check_call('bzr ' + cmd, **kw)


def git(cmd, **kw):
    check_call('git ' + cmd, **kw)


def hg(cmd, **kw):
    check_call('hg ' + cmd, **kw)


def check_call(cmd, **kw):
    log.debug(cmd)
    args = shlex.split(cmd)
    subprocess.check_call(args, **kw)


def check_output(cmd, **kw):
    args = shlex.split(cmd)
    output = subprocess.check_output(args, **kw).strip()
    log.debug('%s: %s', cmd, output)
    return output


FETCHERS = [
    BzrFetcher,
    BzrMergeProposalFetcher,
    GithubFetcher,
    BitbucketFetcher,
    LocalFetcher,
]


def get_fetcher(url, revision):
    for fetcher in FETCHERS:
        matchdict = fetcher.can_fetch(url)
        if matchdict:
            return fetcher(url, revision, **matchdict)
    raise ValueError('No fetcher for url: %s' % url)
