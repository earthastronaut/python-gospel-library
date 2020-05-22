import re

from distutils.core import setup


def get_version():
    with open('gospellibrary/__init__.py') as f:
        for line in f:
            if line.startswith('__version__'):
                match = re.match(r'__version__ =[\'" ]*(\d+)\.(\d+)\.(\d+)[\'" ]*', line)
                major, minor, patch = match.groups()
                return '.'.join([major, minor, patch])
    raise Exception('Could not find version!')


setup(
    name='python-gospel-library',
    version=get_version(),
    packages=['gospellibrary'],
    license='MIT',
    description='Python package that parses Gospel Library content.',
    long_description=open('README.md').read(),
    install_requires=[
        'requests>=2.4.3',
        'backports.lzma>=0.0.13'
    ],
)
