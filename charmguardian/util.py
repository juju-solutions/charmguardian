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


def get_charm_test_envs():
    return ['local']


def get_bundle_test_envs():
    return ['local']


def timestamp():
    return str(datetime.utcnow())


def get_test_result(tests):
    for test in tests:
        if test.get('test') == 'charm-proof':
            if test['returncode'] > 100:
                return 'fail'
        elif test['returncode'] != 0:
            return 'fail'
    return 'pass'
