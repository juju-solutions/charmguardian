import pkg_resources


def fmt(url, result):
    typ = result.pop('type')
    formatter = get_formatter(typ)
    if not formatter:
        return result
    return formatter.fmt(url, result)


def get_formatter(typ):
    for ep in pkg_resources.iter_entry_points('charmguardian.formatters'):
        if ep.name == typ:
            return ep.load()()
    return None


class BundleFormatter(object):
    def fmt(self, url, result):
        bundle = {
            'url': url,
            'tests': result['tests'],
            'result': result['result'],
            'revision': result['revision'],
            'started': result['started'],
            'finished': result['finished'],
        }
        result['tests'] = {
            'charm': {},
            'bundle': {
                url: bundle,
            }
        }
        return result


class CharmFormatter(object):
    def fmt(self, url, result):
        for bundle in result['tests']['bundle'].values():
            bundle.pop('type')
        return result
