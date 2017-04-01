# -*- coding: utf-8 -*-
import re
from setuptools import setup

REQUIRES = [
    'webtest'
]

def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ''
    with open(fname, 'r') as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError('Cannot find version information')
    return version

__version__ = find_version('webtest_aiohttp.py')


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content

setup(
    name='webtest-aiohttp',
    version=__version__,
    description='webtest-aiohttp provides integration of WebTest with aiohttp.web applications',
    long_description=read('README.rst'),
    author='Steven Loria',
    author_email='sloria1@gmail.com',
    url='https://github.com/sloria/webtest-aiohttp',
    py_modules=['webtest_aiohttp'],
    install_requires=REQUIRES,
    license='MIT',
    zip_safe=False,
    keywords='webtest-aiohttp webtest aiohttp testing wsgi asyncio',
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Testing',
    ],
)
