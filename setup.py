# vi: fileencoding=utf-8
# Licensed to CRATE Technology GmbH ("Crate") under one or more contributor
# license agreements.  See the NOTICE file distributed with this work for
# additional information regarding copyright ownership.  Crate licenses
# this file to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may
# obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.
#
# However, if you have executed another commercial license agreement
# with Crate these terms will supersede the license and you may use the
# software solely pursuant to the terms of the relevant commercial agreement.

import sys

from setuptools import setup, find_packages

def contents(filename):
    try:
        with open(filename, 'rb') as fp:
            return fp.read().decode('utf-8')
    except Exception:
        return ''


setup(
    name='cstat',
    author='Christian Haudum',
    author_email='christian.haudum@crate.io',
    url='https://github.com/chaudum/crate-top',
    description='A visual stat tool for CrateDB clusters',
    long_description=contents('README.rst') + '\n\n' + contents('CHANGES.rst'),
    platforms=['any'],
    license='Apache License 2.0',
    packages=['cstat'],
    entry_points={
        'console_scripts': [
            'cstat = cstat.repl:main',
        ]
    },
    install_requires=[
        'appdirs',
        'aiopg',
        'colorama',
        'urwid',
    ],
    extras_require={
        'develop': ['pudb'],
    },
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
