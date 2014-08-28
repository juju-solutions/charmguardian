from contextlib import contextmanager
from datetime import datetime
import logging
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time


log = logging.getLogger(__name__)


def bundletester(dir_, env, deployment=None, exclude=None,
                 skip_implicit=False):
    proc_cwd = os.path.join(dir_, '.deployer-branches', env)
    try:
        os.makedirs(proc_cwd)
    except OSError:
        pass

    with juju_env(env):
        debug = log.getEffectiveLevel() == logging.DEBUG

        result_file = os.path.join(dir_, 'result.json')
        log_level = 'DEBUG' if debug else 'ERROR'

        cmd = 'bundletester -F -r json -t {} -e {} -o {} -l {}'.format(
            dir_, env, result_file, log_level)
        if deployment:
            cmd = '{} -d {}'.format(cmd, deployment)
        if exclude:
            cmd = '{} -x {}'.format(cmd, exclude)
        if skip_implicit:
            cmd = '{} -s'.format(cmd)
        args = shlex.split(cmd)
        output = ''

        log.debug('Running bundletester: %s', cmd)
        with tempfile.NamedTemporaryFile() as writer:
            with open(writer.name, 'rb', 1) as reader:
                p = subprocess.Popen(
                    args,
                    stdout=writer,
                    stderr=subprocess.STDOUT,
                    cwd=proc_cwd,
                )
                while p.poll() is None:
                    if debug:
                        sys.stderr.write(reader.read())
                    time.sleep(0.5)
                if debug:
                    sys.stderr.write(reader.read())
                reader.seek(0)
                output = reader.read()

        try:
            with open(result_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            log.exception(e)

        err_result = {
            "executable": [cmd],
            "returncode": p.returncode,
            "duration": 0.0,
            "suite": "",
            "test": "",
            "output": "bundletester failed:\n{}".format(output),
            "dirname": dir_,
        }

        if p.returncode == 3:
            err_result['output'] = "No tests found"
            err_result['returncode'] = 0

        return [err_result]


@contextmanager
def juju_env(env):
    orig_env = os.environ.get('JUJU_ENV', '')
    if env != orig_env:
        log.debug('Updating JUJU_ENV: "%s" -> "%s"', orig_env, env)
        os.environ['JUJU_ENV'] = env
    try:
        yield
    finally:
        if env != orig_env:
            log.debug('Updating JUJU_ENV: "%s" -> "%s"', env, orig_env)
            os.environ['JUJU_ENV'] = orig_env


def get_envs(env_var):
    envs = os.environ.get(env_var, 'local').split(',')
    return [env.strip() for env in envs]


def get_charm_test_envs():
    return get_envs('CHARM_TEST_ENVS')


def get_bundle_test_envs():
    return get_envs('BUNDLE_TEST_ENVS')


def timestamp():
    return datetime.utcnow().isoformat() + 'Z'


def get_test_result(tests):
    for test in tests:
        if test.get('returncode', 0) != 0:
            return 'fail'
    return 'pass'
