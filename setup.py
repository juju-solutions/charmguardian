from setuptools import setup, find_packages


SETUP = {
    'name': "charmguardian",
    'packages': find_packages(),
    'version': "0.1",
    'author': "Tim Van Steenburgh",
    'author_email': "tvansteenburgh@gmail.com",
    'url': "https://github.com/tvansteenburgh/charmguardian",
    'license': "Affero GNU Public License v3",
    'long_description': open('README.md').read(),
    'entry_points': {
        'console_scripts': [
            'charmguardian = charmguardian.cli:main',
        ],
        'charmguardian.formatters': [
            'bundle = charmguardian.formatters:BundleFormatter',
            'charm = charmguardian.formatters:CharmFormatter',
        ],
    }
}


if __name__ == '__main__':
    setup(**SETUP)
