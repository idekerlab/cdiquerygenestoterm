#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()


with open(os.path.join('cdiquerygenestoterm', '__init__.py')) as ver_file:
    for line in ver_file:
        if line.startswith('__version__'):
            version=re.sub("'", "", line[line.index("'"):])

requirements = [
    'requests'
]

test_requirements = [
    'requests-mock'
    # TODO: put package test requirements here
]

setup(
    name='cdiquerygenestoterm',
    version=version,
    description="Maps genes to terms",
    long_description=readme + '\n\n' + history,
    author="Christopher Churas",
    author_email='churas.camera@gmail.com',
    url='https://github.com/idekerlab/cdiquerygenestoterm',
    packages=[
        'cdiquerygenestoterm',
    ],
    package_dir={'cdiquerygenestoterm':
                 'cdiquerygenestoterm'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD license",
    zip_safe=False,
    keywords='cdiquerygenestoterm',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    scripts=['cdiquerygenestoterm/cdiquerygenestotermcmd.py'],
    test_suite='tests',
    tests_require=test_requirements
)
