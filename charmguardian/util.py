from datetime import datetime
import logging
import json
import os
import shlex
import subprocess

log = logging.getLogger(__name__)


def bundletester(dir_, env, deployment=None):
    result_file = os.path.join(dir_, 'result.json')
    cmd = 'bundletester -F -r json -t {} -e {} -o {}'.format(
        dir_, env, result_file)
    if deployment:
        cmd = '{} -d {}'.format(cmd, deployment)
    args = shlex.split(cmd)
    output = ''

    log.debug('Running bundletester: %s', cmd)
    p = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    output, _ = p.communicate()

    try:
        with open(result_file, 'r') as f:
            return json.load(f)
    except ValueError as e:
        if str(e) == 'No JSON object could be decoded':
            return [{
                'exception': output,
                'returncode': p.returncode,
            }]
        raise


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
        if test.get('test') == 'charm-proof':
            if test['returncode'] > 100:
                return 'fail'
        elif test['returncode'] != 0:
            return 'fail'
    return 'pass'
